import numpy as np
from Softmax import softmax

def attention(Q, K, V):
    d_k = K.shape[-1]

    raw_scores = np.dot(Q, np.transpose(K))

    scaled_scores = np.divide(raw_scores, np.sqrt(d_k))

    attention_weights = np.apply_along_axis(softmax, axis=1, arr=scaled_scores)

    return np.dot(attention_weights, V)

X = np.array([
    [1, 0, 1, 0],
    [0, 1, 0, 1],
    [1, 1, 0, 0]
], dtype=float)

Q = K = V = X
output = attention(Q, K, V)
# print(output)