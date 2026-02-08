#!/usr/bin/env python3
# This script traverses all sites in sites.txt and checks for:
#   response time
#   if site is cached
#   mixed content (http:// and https://)
# The results are placed in log.csv
import sys
import argparse
import subprocess
from decimal import Decimal
from datetime import datetime
import requests
import re

# TODO: Make sure all prints also go to log
# Get the current date and time for the log file
current_date_time = datetime.now()
# Format the current date and time
formatted_date_time = current_date_time.strftime("%m-%d-%y %H:%M")

# set global variable defaults
sites_file = "all_sites.txt"  # location of sites to test by default
sites_to_test = (
    []
)  # a list of urls for this test. Either from a file or user provided (-u)
test_for_response_time = True  # option flag to test the response time
test_for_cache = True  # option flag to test for cache
user_provided_urls = False  # option to store user provided urls to test
verbose = False  # option to print all test results
threshold_high = "0.99"  # default load time threshold_high
failures = []  # list to store failures for possible retest
log_results = False  # log the results only if all sites are being tested
mixed_content = True  # test if pages contains http://{url}
log_file_name = "log.csv"  # default log file name
log_load_results = []  # list to store all test results to save at end of tests
log_cache_results = []  # list to store all cache results to save at end of tests
log_mixed_results = []  # list of sites that have mixed content


# parse the args befor running main()
def parse_command_line():
    global sites_file
    global test_for_response_time
    global user_provided_urls
    global threshold_high
    global test_for_cache
    global verbose
    global mixed_content

    # Create the parser
    parser = argparse.ArgumentParser(description="Website Health Check")

    # Turn off mixed content test
    parser.add_argument(
        "-m",
        "--mixed",
        action="store_true",
        help="Turn off mixed content test",
    )
    # Change the file name of the list of sites to be tested. Default list is sites.txt
    parser.add_argument(
        "-f",
        "--file",
        nargs=1,
        type=str,
        help="Website URLs Filename (default sites.txt)",
    )
    # users request to test certain urls
    parser.add_argument(
        "-u",
        "--urls",
        nargs=1,
        type=comma_separated_strings,
        help="Websites to test (URL1, URL2, ...)\nExample: srt -u 'site1.com, site2'",
    )
    # test for cache?
    parser.add_argument(
        "-c",
        "--cache",
        action="store_true",
        help="Test to see if the website is cached?",
    )
    # test both load time and cache
    parser.add_argument(
        "-cr",
        "--cache_and_response",
        action="store_true",
        help="Print both response time and cache status",
    )
    # user change of threshold_high value
    parser.add_argument(
        "-t",
        "--threshold_high",
        nargs=1,
        type=str,
        help="Set Alert threshold_high (default 1.5)",
    )
    # user request to print more test information
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Provide more information on test results",
    )

    # args is used to determine what args were added and what to do withthem
    args = parser.parse_args()

    # check to see if we want to turn off mixed content test
    if args.mixed:
        mixed_content = False

    # Check if site file name was provided.  If not, use default file
    if args.file:
        sites_file = args.file[0]

    # Check if URLs are provided
    if args.urls:
        for url in args.urls:
            user_provided_urls = True

    # Change the threshold_high used to determine if test should be alerted
    if args.threshold_high:
        threshold_high = args.threshold_high[0]
        test_for_response_time = True

    # does user want to test for site cache
    if args.cache:
        test_for_cache = True
        test_for_response_time = False

    # does user want to test for site cache
    if args.cache_and_response:
        test_for_cache = True

    # does user want to see more test result information
    if args.verbose:
        verbose = True


# extract URLs in --url argument (comma seperated)
def comma_separated_strings(user_urls):
    # Extract each url from the comma seperated string and strip spaces
    global sites_to_test
    sites_to_test = [item.strip() for item in user_urls.split(",")]


# main() is called after the variables have been established and args have been set
def main():
    global verbose
    global log_load_results
    global sites_to_test
    # Add the test date and time to the CSV Log file
    with open(log_file_name, "w") as log:
        log.write(f"{formatted_date_time}\n")
    # check if user provided URLs in command line
    if user_provided_urls == True:
        # Usr provided URLs has already been parsed in args module
        test_sites(sites_to_test)
    else:
        # parse sites_file to get a list of the URLs to test.
        try:
            with open(sites_file, "r") as sites_to_test:
                test_sites(sites_to_test)
        except FileNotFoundError:
            print(f"The file {sites_file} was not found.")
        except IOError:
            print(f"An error occurred while reading the file {sites_file}.")
    # ask user if they want a retest
    if len(failures) != 0:
        user_input = input("Do you want to retest the failures? (yes/no): ").lower()
        if user_input in ["yes", "y"]:
            # set verbose to provide more info on next tests
            verbose = True
            # Put sites into retest (avoid loop)
            retest = failures.copy()
            test_sites(retest)
    # Write log_load_results to log file
    with open(log_file_name, "a") as log:
        for item in log_load_results:
            log.write(f"{item}\n")
        for item in log_cache_results:
            log.write(f"{item}\n")
        for item in log_mixed_results:
            log.write(f"{item}\n")


# test the website page
def test_sites(test_these_sites):
    # Print which tests we will run
    if test_for_response_time == True:
        print(f"Testing Load Time with threshold_high of {threshold_high} seconds.")
    try:
        # get the sites to test from test_these_sites
        for site in test_these_sites:
            # test for return code of 200
            # Check the return code.  Also starts Keep Alive timer on server
            curl_command = f"curl -s -I {site}"
            try:
                # Execute the curl command
                result = subprocess.run(
                    curl_command,
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Could not access {site}")
                continue
            if "200" not in result.stdout.splitlines()[0]:
                # header not 200. Print header
                print(f"{site} Header error: {result.stdout.splitlines()[0]}")
                # go to next site
                continue
            # test site for mixed content
            if mixed_content == True:
                return_code = test_page_for_mixed_content((site.strip()))
                if return_code > 0:
                    match return_code:
                        case 1:
                            print(
                                f"{site.strip()} status_code not 200. Testing next site!"
                            )
                            continue
                        case 2:
                            print(
                                f"{site.strip()} does not appear to be a valid website. Testing next site!"
                            )
                            continue
            # test site load time if requested
            if test_for_response_time == True:
                measure_website_load_time(site.strip())
            # test site for cache if requested
            if test_for_cache == True:
                test_if_site_is_cached(site.strip())
    except KeyboardInterrupt:
        print(f"\nExecution interrupted by user.")
    except FileNotFoundError:
        print(f"The file {sites_to_test.name} was not found.")
    except IOError:
        print(f"An error occurred while reading the file {sites_to_test.name}.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while testing load time: {e}")


def test_page_for_mixed_content(url):
    global failures
    global log_mixed_results
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"
            },
        )
        # alert if site returned anyhing other than status code 200
        if response.status_code != 200:
            return 1
        # print(response) #DEBUG:
        content = response.text
        # Verify that content appears to be a real website.
        if sys.getsizeof(content) < 5000:
            return 2
        # search for non secure site url's (i.e. mixed content)
        http_url = re.sub(r"https://", "http://", url)
        matches = re.findall(f"{http_url}", content)
        count = len(matches)
        if count > 0:
            log_mixed_results.append(
                f"{url} has {count} occurrences of insurcure urls."
            )
            print(f"{url} has {count} occurrences of insurcure urls.")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Error during requests to {url} : {err}")
    return 0


def measure_website_load_time(url):
    global failures
    global log_load_results
    # The curl command with the -w flag to measure total time
    curl_command = f"curl -o /dev/null -s -w '%{{time_total}}' {url}"
    try:
        # Execute the curl command
        result = subprocess.run(
            curl_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Get the output which is the total time and convert it to a number
        total_time = Decimal(result.stdout.strip())
        # save the results in a log file
        log_load_results.append(f"{url},{total_time:,.2f}")
        # print the result if threshold_highs are exceeded
        if total_time >= Decimal(threshold_high.strip()) or total_time < 0.17:
            print(f"{url} took {total_time:,.2f} seconds to load")
            # save failures for possible retest
            failures.append(url)
        else:
            if verbose == True:
                print(f"{url}: {total_time:,.2f}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while testing load time: {e}")


def test_if_site_is_cached(url):
    global failures
    global log_cache_results
    site_under_test = []
    # Check if the first line does not contain "DOCTYPE"
    curl_command = f"curl -sv {url} 2>&1 > /dev/null | egrep '< (x-litespeed-cache: hit|x-proxy-cache:|hummingbird-cache|cache-control|HTTP/2)'"
    try:
        # Execute the curl command
        result = subprocess.run(
            curl_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"{url}: {e}")
        print(f"   Site may not exist")
        log_cache_results.append(f"{url} is not cached or does not exist")
        return

    # Check the results to see if Hummingbird cache is implemented
    if (
        "x-litespeed-cache: hit" in result.stdout
        or "hummingbird-cache: Served" in result.stdout
    ):
        if verbose == True:
            print(f"{url} is cached")
            log_cache_results.append(f"{url} is cached")
    else:
        # save to failure in log and print it for the user
        log_cache_results.append(f"{url} is not cached")
        print(f"{url} is not cached")
        lines = result.stdout.split("\n")  # Splitting text into lines
        for line in lines:
            log_cache_results.append(
                (line),
            )
            print(f"   {line}")


if __name__ == "__main__":
    parse_command_line()
    # run the test
    main()
