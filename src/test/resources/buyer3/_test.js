function randomVector(n) {
    const vector = new Array(n);
    for (let i = 0; i < n; i++) {
        vector[i] = Math.random();
    }
    return vector;
}

function randomMatrix(n, m) {
    const matrix = new Array(n);
    for (let i = 0; i < n; i++) {
        matrix[i] = randomVector(m);
    }
    return matrix;
}

function multiplyMatrix(a, b) {
    const rows_a = a.length
    const cols_a = a[0].length;
    const rows_b = b.length;
    const cols_b = b[0].length;

    if (cols_a !== rows_b) {
        throw new Error("Invalid matrix dimensions");
    }

    const c = new Array(rows_a);

    for (let i = 0; i < rows_a; ++i) {
        const row = new Array(cols_b);
        for (let j = 0; j < cols_b; ++j) {
            let s = a[i][0] * b[0][j];
            for (let k = 1; k < cols_a; ++k) {
                s += a[i][k] * b[k][j];
            }
            row[j] = s;
        }
        c[i] = row;
    }

    return c;
}

function relu(a) {
    if (a.length > 0) {
        if (a[0].length > 0) {
            for (let i = 0; i < a.length; ++i) {
                relu(a[i]);
            }
        } else {
            for (let i = 0; i < a.length; ++i) {
                a[i] = Math.max(0, a[i]);
            }
        }
    }

    return a;
}

function singleTest(X, A, B, C, D) {
    let Y = multiplyMatrix(A, X);
    Y = multiplyMatrix(B, Y);
    Y = multiplyMatrix(C, Y);
    Y = multiplyMatrix(D, Y);
    return Y;
}

function test(loops) {
    for (let i = 0; i < loops; i++) {
        const X = relu(randomMatrix(200, 1));
        const A = relu(randomMatrix(200, 200));
        const B = relu(randomMatrix(100, 200));
        const C = relu(randomMatrix(50, 100));
        const D = relu(randomMatrix(1, 50));

        singleTest(X, A, B, C, D);
    }
}

test(1)
