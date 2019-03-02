import numpy as np
import hyperopt
import sklearn

from functools import partial
from sklearn.model_selection import StratifiedKFold
from hyperopt import fmin, tpe, Trials, STATUS_OK


class ClassifierOptimizer(object):

    def __init__(
            self,
            classifier: sklearn.base.ClassifierMixin,
            space: dict,
            metric: sklearn.metrics
    ) -> None:
        """

        :param classifier:
        :param space:
        :param metric:
        """
        self.classifier = classifier
        self.space = space
        self.metric = metric

    def find_best_params(
            self,
            X: np.ndarray,
            y: np.ndarray,
            max_evals: int = 10,
            n_splits: int = 3,
            verbose: bool = True
    ) -> None:
        """

        :param X:
        :param y:
        :param n_splits:
        :param verbose:
        :return:
        """
        best_params = fmin(
            fn=partial(
                self.evaluate_params,
                X=X, y=y, n_splits=n_splits, verbose=verbose
            ),
            space=self.space,
            algo=tpe.suggest,
            max_evals=max_evals
        )
        return best_params

    def evaluate_params(
            self,
            clf_params: dict,
            X: np.ndarray,
            y: np.ndarray,
            n_splits: int = 3,
            verbose: bool = True
    ) -> dict:
        """

        :param X:
        :param y:
        :param clf_params:
        :return:
        """
        self.classifier.set_params(**clf_params)
        score_train, score_valid = [], []
        for train_idx, valid_idx in StratifiedKFold(n_splits=n_splits).split(X, y):
            x_train_fold, x_valid_fold = X[train_idx], X[valid_idx]
            y_train_fold, y_valid_fold = y[train_idx], y[valid_idx]
            self.classifier.fit(x_train_fold, y_train_fold)
            score_train.append(self.metric(y_train_fold, self.classifier.predict(x_train_fold)))
            score_valid.append(self.metric(y_valid_fold, self.classifier.predict(x_valid_fold)))
        mean_score_train = np.mean(score_train)
        mean_score_valid = np.mean(score_valid)
        if verbose:
            msg = 'Train: {score_train:.4f}, valid: {score_valid:.4f}'
            print(msg.format(score_train=mean_score_train, score_valid=mean_score_valid))
        return {
            'loss': 1 - mean_score_valid,
            'status': STATUS_OK,
            'score': {'train': mean_score_train, 'valid': mean_score_valid}
        }