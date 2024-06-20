from flask import Flask, render_template, request
import pandas as pd
import numpy as np

app = Flask(__name__)

# Funções do Simplex
def encontrar_coluna_pivo(dataframe):
    first_row = dataframe.iloc[0]
    column_most_negative = first_row.astype(float).idxmin()
    return column_most_negative

def encontrar_linha_pivo(dataframe, column):
    last_column = dataframe.iloc[:, -1].astype(float)
    pivo_column = dataframe[column].astype(float)
    
    minValue = float('inf')
    row_index = None

    for i, (last_value, pivo_value) in enumerate(zip(last_column[1:], pivo_column[1:]), start=1):
        if pivo_value != 0:
            value = last_value / pivo_value
            if value < minValue:
                minValue = value
                row_index = i

    if row_index is None:
        raise ValueError("Todas as entradas na coluna de pivô são zero ou a coluna de pivô é inválida.")
    
    return dataframe.index[row_index]

def new_board(dataframe, row, column):
    element = dataframe.loc[row, column]
    new_df = dataframe.astype(float)
    new_df.loc[row] = new_df.loc[row] / element
    for i in new_df.index:
        if i != row:
            new_df.loc[i] = new_df.loc[i] - new_df.loc[i][column] * new_df.loc[row]
    return new_df

def atualizar_board(dataframe, row, column):
    dataframe.rename(columns={column: row}, index={row: column}, inplace=True)
    return dataframe

def veificar_parada(dataframe):
    first_row = dataframe.iloc[0]
    if first_row.min() >= 0:
        return True
    else:
        return False
    
def resultado(dataframe_inicial, dataframe_final, num_vars):
    otimo = {}
    columns1 = dataframe_inicial.columns[:num_vars]  
    columns2 = dataframe_final.columns[:num_vars]    
    
    for column in columns1:
        if column in columns2:
            otimo[column] = 0.0
        else:
            if column in dataframe_final.index:
                otimo[column] = dataframe_final.loc[column].iloc[-1]
            else:
                otimo[column] = None 
    return otimo

def lucro_total(dataframe_final):
    return dataframe_final.iloc[0, -1]

def preco_sombra(dataframe_final, num_vars):
    return dataframe_final.iloc[0, num_vars:-1].to_dict()  # Convertendo para dicionário

def viabilidade(dataframe, num_vars, lista_viabilidade):
    tabela_viabilidade = dataframe.iloc[1:, num_vars:]
    num_linhas = tabela_viabilidade.shape[0]
    num_elementos = len(lista_viabilidade)
    function = 0
    
    for i in range(num_linhas):
        for j in range(num_elementos):
            function += tabela_viabilidade.iloc[i, j].astype(float) * lista_viabilidade[j]
        soma = function + tabela_viabilidade.iloc[i, -1].astype(float)
        
        if soma < 0:
            return False
        else:
            function = 0
            
    lucro = dataframe.iloc[0, num_vars:]
    funcao_lucro = 0
    
    for i in range(num_elementos):
        funcao_lucro += lucro.iloc[i].astype(float) * lista_viabilidade[i]
        
    lucro_total = funcao_lucro + lucro.iloc[-1].astype(float)
    return lucro_total


def simplex(dataframe):
    while not veificar_parada(dataframe):
        cpivo = encontrar_coluna_pivo(dataframe)
        lpivo = encontrar_linha_pivo(dataframe, cpivo)
        newdf = new_board(dataframe, lpivo, cpivo)
        dataframe = atualizar_board(newdf, lpivo, cpivo)
    return dataframe

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para entrada de variáveis e restrições
@app.route('/setup', methods=['POST'])
def setup():
    num_vars = int(request.form['num_vars'])
    num_restrictions = int(request.form['num_restrictions'])
    return render_template('input.html', num_vars=num_vars, num_restrictions=num_restrictions)


# Rota para processar os dados do formulário
@app.route('/process', methods=['POST'])
def process():
    columns = request.form.getlist('columns[]')
    rows = request.form.getlist('rows[]')
    values = request.form.getlist('values[]')

    # Reshape dos valores para uma matriz com base nas restrições e variáveis
    num_vars = int(request.form['num_vars'])
    num_restrictions = int(request.form['num_restrictions'])
    values_matrix = np.array(values, dtype=float).reshape((num_restrictions + 1, num_vars + num_restrictions + 1))

    # Criação do DataFrame
    df = pd.DataFrame(values_matrix, columns=columns, index=rows)

    # Aplicação do método Simplex
    result_df = simplex(df)
    
    otimo = resultado(df, result_df, num_vars)
    lucro_otimo_value = lucro_total(result_df)
    preco_sombra_values = preco_sombra(result_df, num_vars)
    
    # Obter a lista de viabilidade do formulário
    lista_viabilidade = request.form.getlist('viabilidade[]')
    lista_viabilidade = [float(value) for value in lista_viabilidade]
    
    # Calcular a viabilidade com a lista fornecida
    viabilidade_result = viabilidade(result_df, num_vars, lista_viabilidade)
    
    # Conversão do DataFrame resultante para HTML
    result_html = result_df.to_html(classes='table table-bordered')

    return render_template('result.html', result=result_html, otimo=otimo, lucro_otimo_value=lucro_otimo_value, preco_sombra=preco_sombra_values, viabilidade_result=viabilidade_result)

if __name__ == '__main__':
    app.run(debug=True)
