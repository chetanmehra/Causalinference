
import numpy as np
import random
import cvxpy as cvx


def SimulateData(N_c, N_t, mu, Sigma, l, u, Gamma):

	"""
	Function that generates random control and treated units.
	Each treated unit is generated by:
		X_t = w' X_c + epsilon,
	where
		X_c ~ N(mu, Sigma), epsilon ~ N(0, Gamma)
	Args:
		N_c = Number of control units
		N_t = Number of treated units
		mu = k-dimensional mean covariate value of control units
		Sigma = k-by-k covariance matrix of covariates of control units
		l = Minimum number of non-zero weights on the control units
		u = Maximum number of non-zero weights on the control units
		Gamma = k-by-k covariance matrix of normal, zero-mean error term
	Returns:
		X_c = N_c-by-k matrix of generated control units
		X_t = N_t-by-k matrix of generated treated units
		W = N_t-by-N_c matrix of weights put on control units
	"""

	# covariates of controls
	X_c = np.random.multivariate_normal(mean=mu, cov=Sigma, size=N_c)

	W = np.zeros(shape=(N_t, N_c))  # matrix of weights

	# number of non-zero weights for each X_t, generated randomly
	n = np.random.randint(low=l, high=u, size=N_t)

	for i in xrange(N_t):

		# controls that get non-zero weights
		random_index = random.sample(xrange(N_c), n[i])

		# generate weights, then standardize to sum to 1
		non_standardized = np.random.uniform(size=n[i])

		W[i, random_index] = non_standardized / non_standardized.sum()

	k = len(mu)  # generate X_t below
	X_t = np.dot(W, X_c) + np.random.multivariate_normal(mean=np.zeros(k), cov=Gamma, size=N_t)

	return X_c, X_t, W


def EstimateWeights(X_c, X_t):

	"""
	Function that estimates synthetic control weights for each treated unit.
	For each treated unit, we find w that minimizes:
		|| w' X_c - X_t ||_2,
	subject to the weights being between 0 and 1, and that they sum to 1.
	Convex optimization problem solved by calling CVX.
	Args:
		X_c = N_c-by-k matrix of control units
		X_t = N_t-by-k matrix of treated units
	Returns:
		W_hat = N_t-by-N_c matrix of estimated weights
	"""

	N_c = len(X_c)
	if len(X_t.shape) == 1:  # check if input is 1D-array
		N_t = 1
	else:
		N_t = len(X_t)  # there has to be a more elegant way of doing this

	W_hat = np.zeros(shape=(N_t, N_c))  # matrix of weight estimates

	for i in xrange(N_t):

		# for each treated unit, call CVX to solve optimization problem
		w = cvx.Variable(N_c)
		objective = cvx.Minimize(cvx.sum_squares(X_c.T * w - X_t[i, ]))
		constraints = [0 <= w, w <= 1, cvx.sum_entries(w) == 1]  # convex weights
		prob = cvx.Problem(objective, constraints)
		min_value = prob.solve()

		W_hat[i, ] = w.value.getA1()  # convert to flattened array and store

	return W_hat


def main():

	N_c, N_t, k = 5, 3, 2  # set parameters
	mu, Sigma, l, u, Gamma = np.zeros(k), np.identity(k), 2, N_t, np.identity(k)
	
	X_c, X_t, W = SimulateData(N_c, N_t, mu, Sigma, l, u, Gamma)
	W_hat = EstimateWeights(X_c, X_t)

	print 'Actual weights:'
	print W
	print 'Estimated weights:'
	print W_hat

	# estimate weights using mean of X_t as the lone treated unit
	w = EstimateWeights(X_c, X_t.mean(axis=0))

	print 'Averaged weights:'
	print W_hat.mean(axis=0)
	print 'Estimated weights using averaged X_t:'
	print w.flatten()


if __name__ == '__main__':
	main()
