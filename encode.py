from loguru import logger
from reed_muller import ReedMuller

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        logger.error("Usage: {} r m word [word [...]]", sys.argv[0])
        sys.exit(1)

    r, m = map(int, sys.argv[1:3])
    if m <= r:
        logger.error("We require r < m.")
        sys.exit(2)

    rm = ReedMuller(r, m)
    k = rm.message_length()

    for word in sys.argv[3:]:
        try:
            listword = list(map(int, word))
            if not set(listword).issubset([0, 1]) or len(listword) != k:
                logger.error(
                    "FAIL: word {} is not a 0-1 string of length {}", word, k
                )
            else:
                logger.info(
                    "Encoded word: {}", "".join(map(str, rm.encode(listword)))
                )
        except Exception:
            logger.error(
                "FAIL: word {} is not a 0-1 string of length {}", word, k
            )
