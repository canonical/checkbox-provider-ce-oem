# This is the readme file for crypto related jobs.
We have two kind of crypto test. One is for generic another is for accelerator.
1. Generic
    - cryptoinfo
    - ce-oem-crypto/cryptsetup_benchmark
    - ce-oem-crypto/af_alg_hash_crc64_test
    - ce-oem-crypto/af_alg_hash_sha256_test
    - ce-oem-crypto/af_alg_aead_gcm_aes_test
    - ce-oem-crypto/af_alg_skcipher_cbc_aes_test
    - ce-oem-crypto/af_alg_rng_stdrng_test
    - ce-oem-crypto/hwrng-current
2. Accelerator
    - ce-oem-crypto/caam/rng-available
    - ce-oem-crypto/caam/caam_hwrng_test
    - ce-oem-crypto/caam/algo_check
    - ce-oem-crypto/check-caam-priority
    - ce-oem-crypto/check-mcrc-priority
    - ce-oem-crypto/check-sa2ul-priority

## Test jobs
This section will talk about the jobs.

### id: cryptoinfo
This job is a resource job and it will dump out the content of */proc/crypto*

### id: ce-oem-crypto/cryptsetup_benchmark
This job is a job to test cryptographic benchmark by using tool *cryptsetup*.
The test result will be focus on *aes-xts 512b*, which is the cipher used by Ubuntu Core FDE.
```
eg: ubuntu@ubuntu:~$ sudo cryptsetup luksDump /dev/mmcblk3p5
LUKS header information
Version:        2
Epoch:          4
Metadata area:  2097152 [bytes]
Keyslots area:  2621440 [bytes]
UUID:           f4877ac8-a501-42de-857e-02e7d4384386
Label:          ubuntu-data-enc
Subsystem:      (no subsystem)
Flags:          (no flags)

Data segments:
  0: crypt
        offset: 7340032 [bytes]
        length: (whole device)
        cipher: aes-xts-plain64
        sector: 512 [bytes]

Keyslots:
  0: luks2
        Key:        512 bits
        Priority:   preferred
        Cipher:     aes-xts-plain64
        Cipher key: 512 bits
        PBKDF:      argon2i
        Time cost:  4
        Memory:     32
        Threads:    1
        Salt:       1d a1 25 80 ad a6 b1 81 c7 46 fa 3a 1e f9 93 b2 
                    df 74 a3 45 46 d5 2e 61 89 1c 71 dd 41 1f 6c 0e 
        AF stripes: 4000
        AF hash:    sha256
        Area offset:4194304 [bytes]
        Area length:258048 [bytes]
        Digest ID:  0
Tokens:
Digests:
  0: pbkdf2
        Hash:       sha256
        Iterations: 1000
        Salt:       13 c9 ce 61 7e 47 f8 6e 9f be 61 4b 2b 9c f0 69 
                    08 ff a6 52 1a 8d 59 fc 83 f3 fb 68 54 3c 56 d3 
        Digest:     da db 41 09 dc ac e0 3f 9d 56 3b 2e ac 2e 5b 26 
                    54 06 cd ba 58 52 d2 77 e2 31 c3 60 8f 9b 8b b5 
```
### id: ce-oem-crypto/af_alg{cipher}
Those AF_ALG related jobs is testing kernel crypto API can using specific cipher.

### id: ce-oem-crypto/hwrng-current
This job is checking the currently used Hardware Random Number Generator, which is the expected one. This job has a dependency with checkbox config variable *HWRNG*.
```
    eg: HWRNG = rng-caam
        or
        HWRNG = hwrng-hse
```
