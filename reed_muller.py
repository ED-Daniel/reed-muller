import operator
import itertools
from functools import reduce
from loguru import logger


def _binom(n, k):
    return reduce(operator.mul, range(n - k + 1, n + 1)) // reduce(
        operator.mul, range(1, k + 1)
    )


def _construct_vector(m, i):
    return ([1] * (2 ** (m - i - 1)) + [0] * (2 ** (m - i - 1))) * (2**i)


def _vector_mult(*vecs):
    assert len(set(map(len, vecs))) == 1
    return list(map(lambda a: reduce(operator.mul, a, 1), zip(*vecs)))


def _vector_add(*vecs):
    assert len(set(map(len, vecs))) == 1
    return list(map(lambda a: reduce(operator.add, a, 0), zip(*vecs)))


def _vector_neg(x):
    return list(map(lambda a: 1 - a, x))


def _vector_reduce(x, modulo):
    return list(map(lambda a: a % modulo, x))


def _dot_product(x, y):
    assert len(x) == len(y)
    return sum(_vector_mult(x, y))


def _generate_all_rows(m, S):
    if not S:
        return [[1] * (2**m)]

    i, Srest = S[0], S[1:]
    Srest_rows = _generate_all_rows(m, Srest)
    xi_row = _construct_vector(m, i)
    not_xi_row = _vector_neg(xi_row)
    return [_vector_mult(xi_row, row) for row in Srest_rows] + [
        _vector_mult(not_xi_row, row) for row in Srest_rows
    ]


class ReedMuller:
    def __init__(self, r, m):
        self.r, self.m = r, m
        self._construct_generator_matrix()
        self.k = len(self.G[0])
        self.n = 2**m

    def strength(self):
        return 2 ** (self.m - self.r - 1) - 1

    def message_length(self):
        return self.k

    def block_length(self):
        return self.n

    def _construct_generator_matrix(self):
        x_rows = [_construct_vector(self.m, i) for i in range(self.m)]
        self.matrix_by_row = [
            reduce(_vector_mult, [x_rows[i] for i in S], [1] * (2**self.m))
            for s in range(self.r + 1)
            for S in itertools.combinations(range(self.m), s)
        ]
        self.voting_rows = [
            _generate_all_rows(
                self.m, [i for i in range(self.m) if i not in S]
            )
            for s in range(self.r + 1)
            for S in itertools.combinations(range(self.m), s)
        ]
        self.row_indices_by_degree = [0]
        for degree in range(1, self.r + 1):
            self.row_indices_by_degree.append(
                self.row_indices_by_degree[degree - 1] + _binom(self.m, degree)
            )
        self.G = list(zip(*self.matrix_by_row))

    def encode(self, word):
        assert len(word) == self.k
        return [_dot_product(word, col) % 2 for col in self.G]

    def decode(self, eword):
        word = [-1] * self.k

        for degree in range(self.r, -1, -1):
            upper_r = self.row_indices_by_degree[degree]
            lower_r = (
                0
                if degree == 0
                else self.row_indices_by_degree[degree - 1] + 1
            )

            for pos in range(lower_r, upper_r + 1):
                votes = [
                    _dot_product(eword, vrow) % 2
                    for vrow in self.voting_rows[pos]
                ]

                if votes.count(0) == votes.count(1):
                    return None

                word[pos] = 0 if votes.count(0) > votes.count(1) else 1

            s = [
                _dot_product(
                    word[lower_r:upper_r + 1], column[lower_r:upper_r + 1]
                )
                % 2
                for column in self.G
            ]
            eword = _vector_reduce(_vector_add(eword, s), 2)

        return word

    def __repr__(self):
        return "<Reed-Muller code RM(%s,%s), strength=%s>" % (
            self.r,
            self.m,
            self.strength(),
        )


def _generate_all_vectors(n):
    v = [0] * n
    while True:
        yield v
        v[n - 1] += 1
        pos = n - 1
        while pos >= 0 and v[pos] == 2:
            v[pos] = 0
            pos -= 1
            if pos >= 0:
                v[pos] += 1
        if v == [0] * n:
            break


def _characteristic_vector(n, S):
    return [0 if i not in S else 1 for i in range(n)]


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        logger.error("Usage: {} r m", sys.argv[0])
        sys.exit(1)
    r, m = map(int, sys.argv[1:])
    if m <= r:
        logger.error("We require r > m.")
        sys.exit(2)

    rm = ReedMuller(r, m)
    strength = rm.strength()
    message_length = rm.message_length()
    block_length = rm.block_length()

    error_vectors = [
        _characteristic_vector(block_length, S)
        for numerrors in range(strength + 1)
        for S in itertools.combinations(range(block_length), numerrors)
    ]

    success = True
    for word in _generate_all_vectors(message_length):
        codeword = rm.encode(word)

        for error in error_vectors:
            error_codeword = _vector_reduce(_vector_add(codeword, error), 2)
            error_word = rm.decode(error_codeword)
            if error_word != word:
                logger.error(
                    "ERROR: encode({}) => {}, decode({}+{}={}) => {}",
                    word,
                    codeword,
                    codeword,
                    error,
                    error_codeword,
                    error_word,
                )
                success = False

    if success:
        logger.info("RM({},{}): success.", r, m)
