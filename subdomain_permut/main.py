import argparse
import sys
import psutil
import gc
from tqdm import tqdm
import os

# globals
global global_keywords, global_args
global_keywords = []
global_args = None
global_arr_buffer_size = 0

def dedupe_file(file):
    with open(file, 'r') as f:
        lines = f.readlines()

    unique_lines = sorted(set(line.strip() for line in lines if line.strip()))

    with open(file, 'w') as f:
        for line in unique_lines:
            f.write(f"{line}\n")

def parse_args():
    parser = argparse.ArgumentParser(description="Subdomain permutation tool")
    parser.add_argument('--list', '-l', required=True, help='Subdomains list')
    parser.add_argument('--domain', '-d', required=True, help="Domain name for the target")
    parser.add_argument('--level', type=int, default=2, help="Number of iterations to run through (default=2)")
    parser.add_argument('--output', '-o', default='permut.txt', help='Output file name (default=permut.txt)')
    parser.add_argument('--enrich', '-e', help='Enrich using given wordlist')
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    args = parser.parse_args()
    return args

def get_keywords(args) -> list:
    """
    generate a list of keywords
    """
    all_keywords = []
    with open(args.list, 'r') as file:
        for line in file:
            line = line.rstrip()
            local_keywords = line.split('.')

            # also split on hyphens
            for keyword in local_keywords:
                if '-' in keyword:
                    hyphen_keywords = keyword.split('-')
                    local_keywords = local_keywords + hyphen_keywords
            all_keywords = all_keywords + local_keywords
    return list(set(all_keywords))

def count_lines(filepath):
    with open(filepath, 'r') as f:
        return sum(1 for _ in f)

def permut_sub_sub(args, keywords) -> None:
    """
    generate a permutation for subdomain with subdomain
    """
    if args.verbose:
        print('[*] Generating sub-sub permutation')

    with open(args.output, 'a') as file:
        # sub.domain
        for keyword in tqdm(keywords, desc="[*] Initial permutation"):
            file.write(f"{keyword}.{args.domain}\n")
    
    if args.level == 1:
        return
    
    # max array size for in-memory buffer
    max_arr_length = memory_load_test(args)
        
    # dedupe file
    dedupe_file(args.output)

    # generate next levels of permutation
    buffer_array = []
    for _ in range(args.level-1):
        if args.verbose:
            print(f'[*] Starting level {_+2}')
        # empty buffer array if any exist
        if len(buffer_array) != 0:
            if args.verbose:
                print(f'[*] Clearing buffer from previous iteration')
            with open(args.output, 'a') as f:
                f.writelines(buffer_array)
            del buffer_array
            gc.collect()
            buffer_array = []
        # read through previous level permut and add subs
        line_count = count_lines(args.output)
        with open(args.output, 'r') as existing_file:
            for subdomain in tqdm(existing_file, desc=f'[*] Level {_+2}', total=line_count):
                subdomain = subdomain.rstrip()
                for keyword in keywords:
                    buffer_array.append(f"{keyword}.{subdomain}\n")
                    if len(buffer_array) > max_arr_length:
                        with open(f'.{args.output}', 'a') as f: # write to temp file instead of main file
                            f.writelines(buffer_array)
                        del buffer_array
                        gc.collect()
                        buffer_array = []
        
        # flush buffer array
        if len(buffer_array) != 0:
            with open(f'.{args.output}', 'a') as f:
                f.writelines(buffer_array)
            del buffer_array
            gc.collect()
            buffer_array = []
        
        # write contents of temporary file into main file
        temp_arr = []
        with open(f'.{args.output}', 'r') as file1:
            for output_line in tqdm(file1, desc=f'[*] Writing level {_+2}', total=count_lines(f'.{args.output}')):
                if len(temp_arr) < max_arr_length: # store in temp array
                    temp_arr.append(output_line.rstrip())
                else:
                    with open(args.output, 'a') as file2: # flush the temp array, then store in it
                        file2.writelines(temp_arr)
                        del temp_arr
                        gc.collect()
                        temp_arr = [output_line.rstrip()]
        
        # flush temp array
        if len(temp_arr) != 0:
            with open(args.output, 'a') as file:
                file.writelines(temp_arr)
                del temp_arr

        # remove temporary file
        os.remove(f'.{args.output}')
    
        # flush buffer array
        if len(buffer_array) != 0:
            with open(args.output, 'a') as f:
                f.writelines(buffer_array)
            del buffer_array
            gc.collect()
            buffer_array = []
        if args.verbose:
            print(f'[*] All temporary resources freed by level {_+2}')

def memory_load_test(args) -> int:
    """Perform load test on memory to find out how much can be stored in buffer"""
    # first get the available RAM of the system
    available_bytes = psutil.virtual_memory().available
    target_memory = int(available_bytes * 0.8)
    available_gb = available_bytes / (1024 ** 3)
    target_gb = target_memory / (1024 ** 3)
    
    print(f'[i] Available Memory   : {round(available_gb, 2)} GB')
    print(f'[i] Expected Usage     : {round(target_gb, 2)} GB')

    # create sample array, and get the array size
    sample_array = []
    sample_text = f'mylongsamplesubdomainname.{args.domain}'
    process = psutil.Process()
    used_memory = 0
    while True:
        sample_array.append(sample_text)
        used_memory = process.memory_info().rss
        if used_memory >= target_memory:
            max_arr_length = len(sample_array)
            break
        if len(sample_array) == 10000:
            # get the size of array
            arr_size = sys.getsizeof(sample_array) + sum(sys.getsizeof(i) for i in sample_array)
            # calculate array length
            max_arr_length = int((target_memory / arr_size)*10000)
            break
    del sample_array
    gc.collect()
    return max_arr_length

def main():
    args = parse_args()

    if args.verbose:
        print(f'[i] Domain             : {args.domain}')
        print(f'[i] Output file        : {args.output}')
        print(f'[i] Level              : {args.level}')
    
    open(args.output, 'w').write('')
    # get keywords from subdomains file
    keywords = get_keywords(args)

    if args.enrich:
        with open(args.enrich, 'r') as file:
            for line in file:
                line = line.rstrip()
                if line not in keywords:
                    keywords.append(line)
    
    if args.level > 3:
        print(f'[!] Level >3. File size would be huge. Terminate this (ctrl+c) and re-run if unsure about what you\'re doing')
                    
    # permut subdomains
    permut_sub_sub(args, keywords)

if __name__ == "__main__":
    main()