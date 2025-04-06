import argparse

# globals
global global_keywords, global_args
global_keywords = []
global_args = None

def parse_args():
    parser = argparse.ArgumentParser(description="Subdomain permutation tool")
    parser.add_argument('--list', '-l', required=True, help='Subdomains list')
    parser.add_argument('--domain', '-d', required=True, help="Domain name for the target")
    parser.add_argument('--level', type=int, default=2, help="Number of iterations to run through (default=2)")
    parser.add_argument('--output', '-o', default='permut.txt', help='Output file name (default=permut.txt)')
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

def permut_sub_sub(keywords) -> None:
    """
    generate a permutation for subdomain with subdomain
    """
    if args.verbose:
        print('[*] Generating sub-sub permutation')

    with open(args.output, 'a') as file:
        if args.level == 1:
            # sub.domain
            for keyword in keywords:
                file.write(f"{keyword}.{args.domain}\n")
        else:
            print(f'[e] Invalid level: {args.level}')
            exit(1)

if __name__ == "__main__":

    args = parse_args()

    if args.verbose:
        print(f'[i] Domain       : {args.domain}')
        print(f'[i] Output file  : {args.output}')
        print(f'[i] Level        : {args.level}')

    # get keywords from subdomains file
    keywords = get_keywords(args)

    # permut subdomains
    permut_sub_sub(keywords)