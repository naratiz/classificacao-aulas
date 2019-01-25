import itertools
import warnings
import time
import multiprocessing
from collections import Counter

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from imblearn.combine import SMOTEENN
from imblearn.metrics import classification_report_imbalanced
from imblearn.under_sampling import NeighbourhoodCleaningRule, RandomUnderSampler, EditedNearestNeighbours
from imblearn.over_sampling import RandomOverSampler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, cross_val_predict, StratifiedKFold, \
    StratifiedShuffleSplit
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import confusion_matrix
from sklearn.svm import SVC
from sklearn import tree
from yellowbrick.features import RFECV

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)  # display all columns
pd.set_option('display.width', 2000)  # display all columns

# 1 Iris Setosa, 2 Iris Versicolour, 3 Iris Virginica
# dados_completo = pd.read_csv('../input/iris.csv', encoding='utf-8', delimiter=',')
dados_completo = pd.read_csv('../input/DadosCompletoTransformadoML.csv', encoding='utf-8', delimiter='\t')
dados_completo.drop(dados_completo.columns[0], axis=1, inplace=True)
# dados_completo = pd.read_csv('../input/dados.csv', encoding='utf-8', delimiter='\t')
print(dados_completo.head())

random_state = 42
n_jobs = multiprocessing.cpu_count()  # - 1


def mostrar_quantidade_por_classe(df, classe):
    print(df.loc[df['acabamento'] == classe].info())


def mostrar_correlacao(dados, classe):
    matriz_correlacao = dados.corr()
    print('Correlaçao com ' + classe + '\n', matriz_correlacao[classe].sort_values(ascending=False))

    colunas = ['C', 'F', 'M', 'mat', 'peso', '% class', 'out_inc', 'fab_rac', 'area_conf', 'area_man_80_cob',
               'area_man_20_er', 'id_ind', 'sisbov', 'cont_past', 'lita_trace', 'atest_prog_quali', 'envolvido_org',
               'confi', 'semi_confi', 'suple', 'ferti', 'ifp', 'ilp', 'ilpf', 'lat', 'lon', 'prec', 'acab']
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cax = ax.matshow(matriz_correlacao, vmin=-1, vmax=1)
    fig.colorbar(cax)
    ticks = np.arange(0, 28, 1)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(colunas)
    ax.set_yticklabels(colunas)
    plt.xticks(rotation=90)
    plt.savefig('corr.png')
    plt.show()


# mostrar_correlacao(dados_completo, 'acabamento')
classes_balancear = list([2, 3])
print('Classes para balancear', classes_balancear)
test_size = 0.2
train_size = 0.8
print(((train_size * 100), '/', test_size * 100))
X_completo = dados_completo.drop(['acabamento'], axis=1)
Y_completo = dados_completo['acabamento']
conjunto_treinamento = pd.DataFrame()
conjunto_teste = pd.DataFrame()
split = StratifiedShuffleSplit(n_splits=1, train_size=train_size, test_size=test_size, random_state=random_state)
for trainamento_index, teste_index in split.split(X_completo, Y_completo):
    conjunto_treinamento = dados_completo.loc[trainamento_index]
    conjunto_teste = dados_completo.loc[teste_index]

# balanceador = ClusterCentroids(random_state=random_state)
# balanceador = RandomUnderSampler(random_state=random_state)
# balanceador = NearMiss(version=3)
# balanceador = AllKNN(allow_minority=True)
# balanceador = NeighbourhoodCleaningRule(n_jobs=n_jobs, sampling_strategy=list([2, 3, 4]))
balanceador = EditedNearestNeighbours(n_jobs=n_jobs, kind_sel='mode',
                                      sampling_strategy=classes_balancear, n_neighbors=4)

# balanceador = SMOTE()
# balanceador = ADASYN()
# balanceador = RandomOverSampler()

# balanceador = SMOTEENN(random_state=random_state)
print(balanceador)
# X_treino, Y_treino = balanceador.fit_resample(
#     conjunto_treinamento.drop('acabamento', axis=1),
#     conjunto_treinamento['acabamento'])
# X_treino = pd.DataFrame(data=X_treino, columns=X_completo.columns)
# Y_treino = pd.DataFrame(data=Y_treino, columns=['acabamento'])
#
# X_treino.to_csv('../input/DadosCompletoTransformadoMLBalanceadoX.csv', encoding='utf-8', sep='\t')
# Y_treino.to_csv('../input/DadosCompletoTransformadoMLBalanceadoY.csv', encoding='utf-8', sep='\t')
# exit()
X_treino = pd.read_csv('../input/DadosCompletoTransformadoMLBalanceadoX.csv', encoding='utf-8', delimiter='\t')
X_treino.drop(X_treino.columns[0], axis=1, inplace=True)
Y_treino = pd.read_csv('../input/DadosCompletoTransformadoMLBalanceadoY.csv', encoding='utf-8', delimiter='\t')
Y_treino.drop(Y_treino.columns[0], axis=1, inplace=True)
print(sorted(Counter(Y_treino).items()))

X_teste, Y_teste = conjunto_teste.drop('acabamento', axis=1), conjunto_teste['acabamento']

print('X Treino:', X_treino.head(50))
print('X Treino', X_treino.shape)
print('Y Treino:', Y_treino)
resultado = pd.DataFrame()
resultado["id"] = Y_teste.index
resultado["item.classe"] = Y_teste.values
resultado.to_csv("y_teste.csv", encoding='utf-8', index=False)


def fazer_selecao_features_rfe():
    features = X_treino.columns
    rfe = RFECV(RandomForestClassifier(random_state=random_state, oob_score=True, n_estimators=250,
                                       max_depth=75, max_features='sqrt', min_samples_leaf=1, min_samples_split=2),
                cv=kfold, scoring='accuracy')

    rfe.fit(X_treino, Y_treino.values.ravel())
    print(rfe.poof())
    print("Caraterísticas ordenadas pelo rank RFE:")
    print(sorted(zip(map(lambda x: round(x, 4), rfe.ranking_), features)))
    ranking = sorted(zip(rfe.support_, features))
    print("Características selecionadas", ranking)
    return rfe.transform(X_treino)


num_folds = 5
scoring = 'accuracy'
kfold = StratifiedKFold(n_splits=num_folds, random_state=random_state)
# print(fazer_selecao_features_rfe())
# exit()

# preparando alguns modelos
modelos_base = [
    # ('MNB', MultinomialNB()),
    ('RFC', RandomForestClassifier(random_state=random_state, oob_score=True, n_estimators=250,
                                   max_depth=75, max_features='sqrt', min_samples_leaf=1, min_samples_split=2)),
    # ('DTC', tree.DecisionTreeClassifier()),
    # ('K-NN', KNeighborsClassifier()),  # n_jobs=-1 roda com o mesmo número de cores
    # ('SVM', SVC())
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
    plt.savefig(nome_arquivo)


def gerar_matriz_confusao(modelo, nome, tipo, X_treino, Y_treino):
    # y_pred = cross_val_predict(modelo, X_treino, Y_treino, n_jobs=n_jobs)
    modelo.fit(X_treino, Y_treino.values.ravel())
    y_pred = modelo.predict(X_teste)
    matriz_confusao = confusion_matrix(Y_teste, y_pred)
    print('Matriz de Confusão ' + tipo)
    print(matriz_confusao)
    plot_confusion_matrix(matriz_confusao, nome, [1, 2, 3, 4, 5], True,
                          title='Confusion matrix ' + nome + ', normalized')
    plot_confusion_matrix(matriz_confusao, nome, [1, 2, 3, 4, 5], False, title='Confusion matrix ' + nome)
    print(classification_report_imbalanced(y_true=Y_teste, y_pred=y_pred, digits=4))


def rodar_modelo(modelo, nome, tipo, X_treino, Y_treino):
    cv_resultados = cross_val_score(modelo, X_treino, Y_treino.values.ravel(), cv=kfold, scoring=scoring, n_jobs=n_jobs)
    print('Validação cruzada ' + nome + ' :', cv_resultados)
    print("{0}: ({1:.4f}) +/- ({2:.3f})".format(nome, cv_resultados.mean(), cv_resultados.std()))
    if tipo == 'Balanceado':
        gerar_matriz_confusao(modelo, nome, tipo, X_treino, Y_treino)
    return cv_resultados


def imprimir_acuracia(nome, df_results):
    plt.figure()
    sns.boxplot(y='level_0', x=0, data=df_results, whis=10.0)
    sns.despine(top=True, right=True, left=True)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, pos: "%i%%" % (100 * x)))
    plt.xlabel('Acuracy')
    plt.ylabel('')
    plt.title('Difference in terms of acuracy with ' + nome)
    plt.savefig('acuracia' + nome + '.png')


def rodar_algoritmos():
    inicio = time.time()
    # melhor_modelo = BaggingClassifier(modelo, max_features=28, n_jobs=n_jobs,
    #                                   random_state=random_state)
    melhor_modelo = modelo
    cv_results_balanced = rodar_modelo(melhor_modelo, nome, 'Balanceado', X_treino, Y_treino)
    cv_results_imbalanced = rodar_modelo(melhor_modelo, nome, 'Não Balanceado',
                                         conjunto_treinamento.drop('acabamento', axis=1),
                                         conjunto_treinamento['acabamento'])
    mostrar_features_mais_importantes(melhor_modelo)

    final = time.time()
    print('Tempo de execução do ' + nome + ': {0:.4f} segundos'.format(final - inicio))
    return cv_results_balanced, cv_results_imbalanced


def mostrar_features_mais_importantes(melhor_modelo):
    if nome == 'RFC':
        melhor_modelo.fit(X_treino, Y_treino.values.ravel())
        print('Características mais importantes RFC :')
        feature_importances = pd.DataFrame(melhor_modelo.feature_importances_,
                                           index=X_treino.columns,
                                           columns=['importance']).sort_values('importance', ascending=False)
        print(feature_importances)


for nome, modelo in modelos_base:
    cv_results_balanced, cv_results_imbalanced = rodar_algoritmos()
    df_results = (pd.DataFrame({'Balanced ': cv_results_balanced,
                                'Imbalanced ': cv_results_imbalanced})
                  .unstack().reset_index())
    imprimir_acuracia(nome, df_results)
