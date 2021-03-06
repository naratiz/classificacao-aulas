import itertools
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from imblearn.combine import SMOTEENN
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from imblearn.under_sampling import EditedNearestNeighbours
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.model_selection import cross_val_predict, GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)  # display all columns
pd.set_option('display.width', 2000)  # display all columns

dados_completo = pd.read_csv('../input/DadosCompletoTransformadoML.csv', encoding='utf-8', delimiter='\t')
dados_completo = dados_completo.sample(frac=1).reset_index(drop=True)
dados_completo.drop(dados_completo.columns[0], axis=1, inplace=True)
dados_completo.drop(['other_incentives', 'total_area_confinement', 'area_20_erosion', 'quality_programs',
                     'lfi', 'fertigation'],  # , 'field_supplementation', 'clfi'],
                    axis=1, inplace=True)
print(dados_completo.head())

random_state = 42
n_jobs = 6

balanceador = EditedNearestNeighbours(n_jobs=n_jobs, n_neighbors=5)
# balanceador = SMOTEENN(enn=EditedNearestNeighbours(n_jobs=n_jobs, n_neighbors=5), smote=SMOTE(n_jobs=n_jobs))
# balanceador = SMOTE(n_jobs=n_jobs)
print(balanceador)
X_completo, Y_completo = dados_completo.drop('carcass_fatness_degree', axis=1), \
                         dados_completo['carcass_fatness_degree']

num_folds = 5
scoring = 'accuracy'
kfold = StratifiedKFold(n_splits=num_folds, random_state=random_state)

# preparando alguns modelos
modelos_base = [
    ('MLP', MLPClassifier(random_state=random_state)),
    ('ADA', AdaBoostClassifier(random_state=random_state)),
    ('MNB', MultinomialNB()),
    ('RFC', RandomForestClassifier(random_state=random_state, oob_score=True,
                                   n_estimators=100, class_weight='balanced', n_jobs=n_jobs)),
    ('K-NN', KNeighborsClassifier(n_jobs=n_jobs)),  # n_jobs=-1 roda com o mesmo número de cores
    ('SVM', SVC(gamma='scale', class_weight='balanced', random_state=random_state))
]


def plot_confusion_matrix(cm, nome, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.gray):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    plt.figure()
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        np.set_printoptions(precision=2)
        nome_arquivo = 'matriz_confusao_normalizada_' + nome + '.png'
    else:
        nome_arquivo = 'matriz_confusao_' + nome + '.png'

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="black" if cm[i, j] > thresh else "white")

    plt.ylabel('Actual class')
    plt.xlabel('Predicted class')
    plt.grid('off')
    plt.tight_layout()
    plt.savefig('figuras/' + nome_arquivo)


scores = ['f1_weighted']


def rodar_algoritmos():
    for score in scores:
        pipeline = Pipeline([('bal', balanceador),
                             ('clf', modelo)])
        print("# Tuning hyper-parameters for %s in %s" % (score, nome))
        print()

        np.set_printoptions(precision=4)
        grid_search = GridSearchCV(pipeline, escolher_parametros(), cv=kfold, refit=True, n_jobs=n_jobs,
                                   scoring=score, verbose=2)
        grid_search.fit(X_completo, Y_completo)

        print("Best parameters set found on development set:")
        print()
        print(grid_search.best_params_)
        print()
        print("Grid scores on development set:")
        print()
        means = grid_search.cv_results_['mean_test_score']
        stds = grid_search.cv_results_['std_test_score']
        for mean, std, params in zip(means, stds, grid_search.cv_results_['params']):
            print("%0.4f (+/-%0.04f) for %r"
                  % (mean, std * 2, params))
        print()

        print("Detailed classification report:")
        print()
        print("The model is trained on the full development set.")
        print("The scores are computed on the full evaluation set.")
        print()
        pipeline = Pipeline([('bal', balanceador),
                             ('clf', grid_search.best_estimator_)])
        y_pred = cross_val_predict(pipeline, X_completo, Y_completo, cv=kfold, n_jobs=n_jobs)
        matriz_confusao = confusion_matrix(Y_completo, y_pred)
        plot_confusion_matrix(matriz_confusao, nome + '_' + score, [1, 2, 3, 4, 5], False,
                              title='Confusion matrix' + nome + '(best parameters)')
        plot_confusion_matrix(matriz_confusao, nome + '_' + score, [1, 2, 3, 4, 5], True,
                              title='Confusion matrix ' + nome + ', normalized')
        print('Matriz de Confusão')
        print(matriz_confusao)
        print(classification_report(y_true=Y_completo, y_pred=y_pred, digits=4))
        print()


def escolher_parametros():
    if nome == 'K-NN':
        return [{'clf__weights': ['uniform', 'distance'],
                 'clf__n_neighbors': [1, 2, 3, 4, 5, 10, 15, 20]}
                ]
    elif nome == 'SVM':
        return [{'clf__C': [2 ** 6, 2 ** 7, 2 ** 8],
                 'clf__gamma': [2 ** -3, 2 ** -1, 2 ** 1, 2 ** 3],
                 'clf__kernel': ['rbf']}
                ]
    elif nome == 'MNB':
        return [{'clf__alpha': [1, 0.1, 0.01, 0.001, 0.0001, 0.00001]}
                ]
    elif nome == 'RFC':
        return [{'clf__n_estimators': [100, 250],
                 'clf__min_samples_leaf': [1, 5, 10],
                 'clf__min_samples_split': [2, 5, 10],
                 'clf__max_features': ['sqrt', 'log2', None],
                 'clf__max_depth': [50, 75]}
                ]
    elif nome == 'MLP':
        return [{'clf__alpha': [2 ** -5, 2 ** -4, 2 ** -3, 2 ** -1, 2 ** 1, 2 ** 3],
                 'clf__max_iter': [2 ** 6, 2 ** 7, 2 ** 8, 2 ** 9, 2 ** 10]}
                ]
    elif nome == 'ADA':
        return [{'clf__n_estimators': [2, 2 ** 2, 2 ** 4, 2 ** 6, 2 ** 8, 2 ** 10]}
                ]
    return None


for nome, modelo in modelos_base:
    rodar_algoritmos()
