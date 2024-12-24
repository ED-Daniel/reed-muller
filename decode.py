from loguru import logger
from reed_muller import ReedMuller

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        logger.error("Usage: {} r m codeword [codeword [...]]", sys.argv[0])
        sys.exit(1)

    r, m = map(int, sys.argv[1:3])
    if m <= r:
        logger.error("We require r < m.")
        sys.exit(2)

    rm = ReedMuller(r, m)
    n = rm.block_length()

    for codeword in sys.argv[3:]:
        try:
            listword = list(map(int, codeword))
            if not set(listword).issubset([0, 1]) or len(listword) != n:
                logger.error(
                    "FAIL: word {} is not a 0-1 string of length {}",
                    codeword,
                    n,
                )
            else:
                decodeword = rm.decode(listword)
                if not decodeword:
                    logger.warning(
                        "Could not unambiguously decode word {}", codeword
                    )
                else:
                    logger.info(
                        "Decoded word: {}", "".join(map(str, decodeword))
                    )
        except Exception as e:
            logger.error(
                "Unexpected error while processing word {}: {}", codeword, e
            )
