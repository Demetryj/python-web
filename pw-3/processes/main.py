from multiprocessing import Pool, cpu_count
from time import time


def divisors(num: int) -> list[int]:
    result = []
    for n in range(1, num + 1):
        if num % n == 0:
            result.append(n)
    return result


def factorize_sync(*numbers: int) -> list[list[int]]:
    return [divisors(num) for num in numbers]


def factorize_parallel(*numbers: int) -> list[list[int]]:
    with Pool(processes=cpu_count()) as pool:
        return pool.map(divisors, numbers)


if __name__ == "__main__":
    nums = (128, 255, 99999, 10651060)

    # sync
    t1 = time()
    sync_result = factorize_sync(*nums)
    t2 = time()

    # parallel
    t3 = time()
    parallel_result = factorize_parallel(*nums)
    print(type(parallel_result))
    t4 = time()

    # перевірка
    a, b, c, d = sync_result
    assert a == [1, 2, 4, 8, 16, 32, 64, 128]
    assert b == [1, 3, 5, 15, 17, 51, 85, 255]
    assert c == [1, 3, 9, 41, 123, 271, 369, 813, 2439, 11111, 33333, 99999]
    assert d == [1, 2, 4, 5, 7, 10, 14, 20, 28, 35, 70, 140, 76079, 152158, 304316, 380395, 532553, 760790, 1065106, 1521580, 2130212, 2662765, 5325530, 10651060]

    assert sync_result == parallel_result

    print(f"CPU cores: {cpu_count()}")
    print(f"Sync time: {t2 - t1:.6f}s")
    print(f"Parallel time: {t4 - t3:.6f}s")
