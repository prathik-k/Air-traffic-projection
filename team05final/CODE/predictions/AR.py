import numpy as np

def create_matrices_used_to_compute_parameters(past_statistics, order_AR):
    """
    This function uses past data to return two matrices that will be needed to compute the parameters of the AR model.

    The AR model is defined as :
    Y_{p + 1} = alpha_1 * Y_1 + ... + alpha_p * Y_p
    ...
    Y_{t - 1} = alpha_1 * Y_{t-(p+1)} + ... + alpha_p * Y_{t-2}
    Y_t = alpha_1 * Y_{t-p} + ... + alpha_p * Y_{t-1}

    :param past_statistics: Array representing the past statistics that will be needed to compute the parameters of
    the AR model.     Using the notations presented above we have past_statistics = [Y_1, Y_2, ..., Y_t].
    :param order_AR: Integer representing the order of the AR model, i.e. the number of parameters of the model.
    Using the notations presented above we have order_AR = p..
    :return A, b: arrays such that AX = b where X is the vector containing the parameters of the model and needs to
    be determined. Using the notations presented above we have:
    A = [[Y_1, ..., Y_p],
        ...,
        [Y_{t-(p+1)}, ..., Y_{t-2}],
        [Y_{t-p}, ..., Y_{t-1}]]
    b = [Y_{p + 1},
        ...,
        Y_{t - 1},
        Y_t]
    X = [alpha_1, alpha_2, ..., alpha_p]
    """
    b = past_statistics[order_AR:]
    A = np.zeros((len(b), order_AR))
    for i in range(len(b)):
        for j in range(order_AR):
            A[i][j] = past_statistics[i + j]

    return A, b


def compute_parameters(A, b):
    """
    This function returns the vector of parameters X representing the parameters of the AR model.
    :param A, b: Arrays such that AX = b where X is the vector containing the parameters of the model and needs to be
    determined.
    :return parameters: Array X representing the parameters of the AR model.
    """
    # Since A * X = b we have X = (inverse(transpose(A) * A) * B where inverse(transpose(A) * A is the pseudo-inverse
    # matrix of A
    A_pseudo_inverse = np.linalg.pinv(A)
    parameters = np.dot(A_pseudo_inverse, b)

    return parameters


def create_matrix_for_prediction(past_statistics, order_AR, number_of_next_statistics):
    """
    This function arranges past data into a matrix A. The AR model can then be applied on A to use past statistics to
    compute predictions.
    :param past_statistics: Array containing past data.
    :param order_AR: Integer representing the order of the AR model, i.e. the number of parameters of the model.
    :param number_of_next_statistics: Integer representing the number of next statistics that we wish to predict.
    :return A: Array containing past statistics which can easily be used to predict next statistics.

    For instance if past_statistics = [Y_1, Y_2, Y_3, Y_4, Y_5, Y_6, Y_7], the order of the AR model = 3 and we wish to predict the
    next 4 statistics then:
    A = [[Y_5, Y_6, Y_7],
        [Y_6, Y_7, 0.],
        [Y_7, 0., 0.],
        [0., 0., 0.]]
    """
    A = np.zeros((number_of_next_statistics, order_AR))
    last_past_statistics = past_statistics[len(past_statistics) - order_AR:]
    A[0] = last_past_statistics
    for p in range(1, np.minimum(order_AR, number_of_next_statistics)):
        A[p][:-p] = last_past_statistics[p:]

    return A


def predict_next_statistics(A, parameters, order_AR):
    """
    This function returns predicted values computed using past statistics and an AR model.
    :param A: Array containing past statistics which can easily be used to predict next statistics.
    :param parameters: Array containing the parameters of the AR model.
    :param order_AR: Integer representing the order of the AR model.
    :return b_predicted: Array containing the predicted values.

    One-step ahead prediction is used to predict values.
    For instance if parameters = [alpha_1, alpha_2, alpha_3] and
    A = [[Y_5, Y_6, Y_7],
        [Y_6, Y_7, 0.],
        [Y_7, 0., 0.],
        [0., 0., 0.]]
    Then: b_predicted = [b_1, b_2, b_3, b_4]
    b_1 = Y_5 * alpha_1 + Y_6 * alpha_2 + Y_7 * alpha_3
    b_2 = Y_6 * alpha_1 + Y_7 * alpha_2 + b_1 * alpha_3
    b_3 = Y_7 * alpha_1 + b_1 * alpha_2 + b_2 * alpha_3
    b_4 = b_1 * alpha_1 + b_2 * alpha_2 + b_3 * alpha_3
    """
    # We compute the predicted values using the formula b = A * X where X represents the vector of parameters
    # of the AR model.
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
    """
    This function predicts future values using past data.
    :param past_statistics: Array containing past data.
    :param order_AR: Integer representing the order of the AR model that we wish to use to predict future values.
    :param number_of_next_statistics: Integer representing the number of future values that we wish to predict using
    one-step ahead prediction.
    :return next_statistics: Array containing the predictions of future statistics.
    """
    # We compute the parameters of the AR model using the formula AX = b
    # where X represents the vector of parameters of the AR model.
    A, b = create_matrices_used_to_compute_parameters(past_statistics, order_AR)
    parameters = compute_parameters(A, b)

    # We arrange past data in a matrix which can then easily be used to predict new values
    A_prediction = create_matrix_for_prediction(past_statistics, order_AR, number_of_next_statistics)

    # We compute the predicted values using the formula next_statistics = A_prediction * X where X represents the vector
    # of parameters of the AR model.
    next_statistics = predict_next_statistics(A_prediction, parameters, order_AR)

    return next_statistics
