from flask import Flask, render_template, request  # Importa as bibliotecas Flask para criar a aplicação web e funções para renderizar templates e manipular requisições
import pandas as pd  # Importa a biblioteca pandas para manipulação de dados
import numpy as np  # Importa a biblioteca numpy para operações numéricas

app = Flask(__name__)  # Cria uma instância da aplicação Flask

# Funções do Simplex
def encontrar_coluna_pivo(dataframe):  # Encontra a coluna pivô para o algoritmo Simplex
    first_row = dataframe.iloc[0]  # Obtém a primeira linha do DataFrame
    column_most_negative = first_row.astype(float).idxmin()  # Encontra o índice da coluna com o valor mais negativo
    return column_most_negative  # Retorna o índice da coluna pivô

def encontrar_linha_pivo(dataframe, column):  # Encontra a linha pivô para o algoritmo Simplex
    last_column = dataframe.iloc[:, -1].astype(float)  # Obtém a última coluna do DataFrame como float
    pivo_column = dataframe[column].astype(float)  # Obtém a coluna pivô como float
    
    minValue = float('inf')  # Inicializa o valor mínimo com infinito
    row_index = None  # Inicializa o índice da linha com None

    # Itera sobre as linhas, calculando o valor mínimo positivo da razão entre a última coluna e a coluna pivô
    for i, (last_value, pivo_value) in enumerate(zip(last_column[1:], pivo_column[1:]), start=1):
        if pivo_value != 0:  # Verifica se o valor da coluna pivô não é zero
            value = last_value / pivo_value  # Calcula a razão
            if value < minValue:  # Atualiza o valor mínimo e o índice da linha
                minValue = value
                row_index = i

    if row_index is None:  # Verifica se não foi encontrado um índice válido
        raise ValueError("Todas as entradas na coluna de pivô são zero ou a coluna de pivô é inválida.")
    
    return dataframe.index[row_index]  # Retorna o índice da linha pivô

def new_board(dataframe, row, column):  # Cria um novo quadro atualizado para o algoritmo Simplex
    element = dataframe.loc[row, column]  # Obtém o elemento pivô
    new_df = dataframe.astype(float)  # Converte o DataFrame para float
    new_df.loc[row] = new_df.loc[row] / element  # Divide a linha pivô pelo elemento pivô
    for i in new_df.index:  # Itera sobre as linhas
        if i != row:  # Verifica se a linha não é a linha pivô
            new_df.loc[i] = new_df.loc[i] - new_df.loc[i][column] * new_df.loc[row]  # Atualiza as outras linhas
    return new_df  # Retorna o novo DataFrame

def atualizar_board(dataframe, row, column):  # Atualiza o quadro com os novos nomes de linha e coluna
    dataframe.rename(columns={column: row}, index={row: column}, inplace=True)  # Renomeia a coluna e a linha pivô
    return dataframe  # Retorna o DataFrame atualizado

def veificar_parada(dataframe):  # Verifica se a solução ótima foi alcançada
    first_row = dataframe.iloc[0]  # Obtém a primeira linha do DataFrame
    if first_row.min() >= 0:  # Verifica se todos os valores são maiores ou iguais a zero
        return True  # Retorna verdadeiro se a solução ótima foi alcançada
    else:
        return False  # Retorna falso caso contrário
    
def resultado(dataframe_inicial, dataframe_final, num_vars):  # Calcula os valores ótimos das variáveis
    otimo = {}  # Inicializa um dicionário para armazenar os valores ótimos
    columns1 = dataframe_inicial.columns[:num_vars]  # Obtém as colunas das variáveis no DataFrame inicial
    columns2 = dataframe_final.columns[:num_vars]  # Obtém as colunas das variáveis no DataFrame final
    
    for column in columns1:  # Itera sobre as colunas das variáveis
        if column in columns2:  # Verifica se a coluna está no DataFrame final
            otimo[column] = 0.0  # Define o valor ótimo como 0.0
        else:
            if column in dataframe_final.index:  # Verifica se a coluna está no índice do DataFrame final
                otimo[column] = dataframe_final.loc[column].iloc[-1]  # Obtém o valor ótimo
            else:
                otimo[column] = None  # Define o valor como None se a coluna não estiver presente
    return otimo  # Retorna o dicionário com os valores ótimos

def lucro_total(dataframe_final):  # Calcula o lucro total da solução ótima
    return dataframe_final.iloc[0, -1]  # Retorna o valor da última coluna da primeira linha

def preco_sombra(dataframe_final, num_vars):  # Calcula os preços sombra das variáveis
    return dataframe_final.iloc[0, num_vars:-1].to_dict()  # Converte os valores em um dicionário

def viabilidade(dataframe, num_vars, lista_viabilidade):  # Verifica a viabilidade da solução
    tabela_viabilidade = dataframe.iloc[1:, num_vars:]  # Obtém a parte do DataFrame relacionada à viabilidade
    num_linhas = tabela_viabilidade.shape[0]  # Obtém o número de linhas
    num_elementos = len(lista_viabilidade)  # Obtém o número de elementos na lista de viabilidade
    function = 0  # Inicializa a função de viabilidade
    
    for i in range(num_linhas):  # Itera sobre as linhas da tabela de viabilidade
        for j in range(num_elementos):  # Itera sobre os elementos da lista de viabilidade
            function += tabela_viabilidade.iloc[i, j].astype(float) * lista_viabilidade[j]  # Calcula a função de viabilidade
        soma = function + tabela_viabilidade.iloc[i, -1].astype(float)  # Soma o resultado com o valor da última coluna
        
        if soma < 0:  # Verifica se a soma é negativa
            return False  # Retorna falso se a soma é negativa
        else:
            function = 0  # Reseta a função de viabilidade
            
    lucro = dataframe.iloc[0, num_vars:]  # Obtém a linha de lucro
    funcao_lucro = 0  # Inicializa a função de lucro
    
    for i in range(num_elementos):  # Itera sobre os elementos da lista de viabilidade
        funcao_lucro += lucro.iloc[i].astype(float) * lista_viabilidade[i]  # Calcula a função de lucro
        
    lucro_total = funcao_lucro + lucro.iloc[-1].astype(float)  # Soma o resultado com o valor da última coluna
    return lucro_total  # Retorna o lucro total


def simplex(dataframe):  # Executa o algoritmo Simplex
    while not veificar_parada(dataframe):  # Itera até que a condição de parada seja atendida
        cpivo = encontrar_coluna_pivo(dataframe)  # Encontra a coluna pivô
        lpivo = encontrar_linha_pivo(dataframe, cpivo)  # Encontra a linha pivô
        newdf = new_board(dataframe, lpivo, cpivo)  # Cria um novo quadro
        dataframe = atualizar_board(newdf, lpivo, cpivo)  # Atualiza o quadro
    return dataframe  # Retorna o DataFrame final

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')  # Renderiza a página inicial

# Rota para entrada de variáveis e restrições
@app.route('/setup', methods=['POST'])
def setup():
    num_vars = int(request.form['num_vars'])  # Obtém o número de variáveis do formulário
    num_restrictions = int(request.form['num_restrictions'])  # Obtém o número de restrições do formulário
    return render_template('input.html', num_vars=num_vars, num_restrictions=num_restrictions)  # Renderiza a página de entrada de dados


# Rota para processar os dados do formulário
@app.route('/process', methods=['POST'])
def process():
    columns = request.form.getlist('columns[]')  # Obtém a lista de nomes de colunas do formulário
    rows = request.form.getlist('rows[]')  # Obtém a lista de nomes de linhas do formulário
    values = request.form.getlist('values[]')  # Obtém a lista de valores do formulário

    # Reshape dos valores para uma matriz com base nas restrições e variáveis
    num_vars = int(request.form['num_vars'])  # Obtém o número de variáveis do formulário
    num_restrictions = int(request.form['num_restrictions'])  # Obtém o número de restrições do formulário
    values_matrix = np.array(values, dtype=float).reshape((num_restrictions + 1, num_vars + num_restrictions + 1))  # Converte os valores em uma matriz numpy

    # Criação do DataFrame
    df = pd.DataFrame(values_matrix, columns=columns, index=rows)  # Cria um DataFrame com os valores e nomes de colunas e linhas

    # Aplicação do método Simplex
    result_df = simplex(df)  # Aplica o algoritmo Simplex ao DataFrame
    
    otimo = resultado(df, result_df, num_vars)  # Calcula os valores ótimos
    lucro_otimo_value = lucro_total(result_df)  # Calcula o lucro total
    preco_sombra_values = preco_sombra(result_df, num_vars)  # Calcula os preços sombra
    
    # Obter a lista de viabilidade do formulário
    lista_viabilidade = request.form.getlist('viabilidade[]')  # Obtém a lista de viabilidade do formulário
    lista_viabilidade = [float(value) for value in lista_viabilidade]  # Converte os valores para float
    
    # Calcular a viabilidade com a lista fornecida
    viabilidade_result = viabilidade(result_df, num_vars, lista_viabilidade)  # Calcula a viabilidade
    
    # Conversão do DataFrame resultante para HTML
    result_html = result_df.to_html(classes='table table-bordered')  # Converte o DataFrame para HTML

    return render_template('result.html', result=result_html, otimo=otimo, lucro_otimo_value=lucro_otimo_value, preco_sombra=preco_sombra_values, viabilidade_result=viabilidade_result)  # Renderiza a página de resultados

if __name__ == '__main__':
    app.run(debug=True)  # Executa a aplicação Flask em modo debug
