import numpy as np

def softmax(x):
    sum_of_e_exponents = np.sum(np.exp(x))

    softmax = np.exp(x) / sum_of_e_exponents

    return softmax

# print(np.round(softmax(np.array([1.0, 0.0, 0.5])), 3))