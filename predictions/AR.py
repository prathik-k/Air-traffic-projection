import numpy as np

def create_matrices_used_to_compute_parameters(past_statistics, order_AR):
    b = past_statistics[order_AR:]
    A = np.zeros((len(b), order_AR))
    for i in range(len(b)):
        for j in range(order_AR):
            A[i][j] = past_statistics[i + j]
    return A, b


def compute_parameters(A, b):
    A_pseudo_inverse = np.linalg.pinv(A)
    parameters = np.dot(A_pseudo_inverse, b)
    return parameters


def create_matrix_for_prediction(past_statistics, order_AR, number_of_next_statistics):
    A = np.zeros((number_of_next_statistics, order_AR))
    last_past_statistics = past_statistics[len(past_statistics) - order_AR:]
    A[0] = last_past_statistics
    for p in range(1, np.minimum(order_AR, number_of_next_statistics)):
        A[p][:-p] = last_past_statistics[p:]
    return A


def predict_next_statistics(A, parameters, order_AR):
    b_predicted = [np.dot(A[0], parameters)]
    for k in range(0, len(A) - 1):
        if (len(b_predicted) < order_AR):
            for j in range(len(b_predicted)):
                A[k + 1][-1 - j] = b_predicted[k - j]
            b_predicted.append(np.dot(A[k + 1], parameters))
        else:
            for j in range(order_AR):
                A[k + 1][-1 - j] = b_predicted[k - j]
            b_predicted.append(np.dot(A[k + 1], parameters))
    b_predicted = np.array(b_predicted).astype(int)
    return b_predicted


def full_prediction_AR(past_statistics, order_AR, number_of_next_statistics):
    A, b = create_matrices_used_to_compute_parameters(past_statistics, order_AR)
    parameters = compute_parameters(A, b)

    A_prediction = create_matrix_for_prediction(past_statistics, order_AR, number_of_next_statistics)

    next_statistics = predict_next_statistics(A_prediction, parameters, order_AR)
    return next_statistics
