#!/usr/bin/python3
import argparse
from collections import OrderedDict


def read_crypto_info():
    with open("/proc/crypto", "r") as fp:
        data = fp.read()

    return data


def crypto_info_parser(crypto_raw):
    crypto_info = OrderedDict()

    for data in crypto_raw.strip("\n").split("\n\n"):
        tmp_dict = {}
        for item in data.strip().split("\n"):
            key, value = item.split(":")
            tmp_dict.update({key.strip(): value.strip()})

        name = tmp_dict.pop("name")
        priority = int(tmp_dict.pop("priority"))
        driver = tmp_dict.pop("driver")
        type = tmp_dict.pop("type")
        key = "{}_{}".format(type, name)
        if crypto_info.get(key) is None:
            crypto_info.update({key: {}})
        if crypto_info[key].get(priority) is None:
            crypto_info[key][priority] = []
        crypto_info[key][priority].append(driver)

    return crypto_info


def check_crypto_driver_priority(type, name, driver_pattern):
    result = True

    crypto_info = crypto_info_parser(read_crypto_info())
    algo_key = "{}_{}".format(type, name)
    print(
        "\n# Checking AF_ALG {} type with {} algorithm is supported: ".format(
            type, name
        ),
        end=""
    )
    if algo_key in crypto_info.keys():
        print("Yes")
    else:
        print("Failed")
        return False

    match_drivers = []
    max_priority = max(crypto_info[algo_key].keys())

    print("all supported driver for {} - {}".format(type, name))
    print("  Priority\tDriver")
    for priority, drivers in crypto_info[algo_key].items():
        for driver in drivers:
            print("- {}\t\t{}".format(priority, driver))
            if driver.find(driver_pattern) != -1:
                match_drivers.append(driver)

    print(
        "\n# Checking drivers match to '{}' pattern: ".format(driver_pattern),
        end=""
    )
    if match_drivers:
        print("Yes")
    else:
        print("Failed")
        return False

    priority_drivers = crypto_info[algo_key][max_priority]
    target_dr = [dr for dr in match_drivers if dr in priority_drivers]

    print("\n# Checking matched driver is highest priority: ", end="")
    if target_dr:
        print("Yes")
    else:
        print("Failed")
        result = False

    return result


class TestCryptoDriver():

    @staticmethod
    def check_caam_drivers():
        check_list = [
            ("hash", "sha256", "caam"),
            ("skcipher", "cbc(aes)", "caam"),
            ("aead", "gcm(aes)", "caam"),
            ("rng", "stdrng", "caam")
        ]

        if all([check_crypto_driver_priority(*data) for data in check_list]):
            print("All CAAM crypto drivers is supported")
        else:
            raise SystemExit("Some CAAM crypto drivers is not supported")

    @staticmethod
    def check_mcrc_drivers():
        if check_crypto_driver_priority("shash", "crc64", "mcrc"):
            print("TI mcrc driver is supported")
        else:
            raise SystemExit("TI mcrc is not supported")

    @staticmethod
    def check_sa2ul_drivers():
        check_list = [
            ("ahash", "sha256", "sa2ul"),
            ("skcipher", "cbc(aes)", "sa2ul"),
            ("aead", "authenc(hmac(sha256),cbc(aes))", "sa2ul")
        ]

        if all([check_crypto_driver_priority(*data) for data in check_list]):
            print("All SA2UL crypto drivers is supported")
        else:
            raise SystemExit("Some SA2UL crypto drivers is not supported")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--type",
        choices=["caam", "sa2ul", "mcrc"],
        help='Validate specific crypto driver module',
    )
    args = parser.parse_args()
    getattr(TestCryptoDriver, "check_{}_drivers".format(args.type))()


if __name__ == "__main__":
    main()
