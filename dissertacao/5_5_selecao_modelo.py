import itertools
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)  # display all columns
pd.set_option('display.width', 2000)  # display all columns


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
        nome_arquivo = 'matriz_confusao_normalizada_' + nome + '_smoteenn.png'
    else:
        nome_arquivo = 'matriz_confusao_' + nome + '_smoteenn.png'

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




matriz_confusao = np.array(
[[  4001,    838,    122,     85,      2],
 [ 17561, 291800,  98334,  17504,     39],
 [  8233, 149992, 335089,  69731,    245],
 [   361,   1855,   6471,  53746,    340],
 [     2,      1,      2,     66,    166]]
)
# nome = 'MNB'
# nome = 'RFC'
nome = 'K-NN'
# nome = 'SVM'
plot_confusion_matrix(matriz_confusao, nome, [1, 2, 3, 4, 5], False,
                      title='Confusion matrix ' + nome)
plot_confusion_matrix(matriz_confusao, nome, [1, 2, 3, 4, 5], True,
                      title='Confusion matrix ' + nome + ', normalized')
