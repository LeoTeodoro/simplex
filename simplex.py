import numpy as np
import pandas as pd

arr = np.array([-80,-70,-100,-16,0,0,0,0,
                1,1,1,4,1,0,0,250,
                0,1,1,2,0,1,0,600,
                3,2,4,0,0,0,1,500])
arr = arr.reshape(4,8)

df = pd.DataFrame(columns=['E','M','A','P','X1','X2','X3','LD'],
                  index=['Z','X1','X2','X3'],
                  data=arr)

def encontrar_coluna_pivo(dataframe):
    first_row = dataframe.iloc[0]

    column_most_negative =first_row.astype(float).idxmin()

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
    new_df.loc[row] = new_df.loc[row]/element
    for i in new_df.index:
        if i != row:
            new_df.loc[i] = new_df.loc[i] - new_df.loc[i][column]*new_df.loc[row]
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

def simplex(dataframe):
    while not veificar_parada(dataframe):
        cpivo = encontrar_coluna_pivo(dataframe)
        lpivo = encontrar_linha_pivo(dataframe, cpivo)
        newdf = new_board(dataframe, lpivo, cpivo)
        dataframe = atualizar_board(newdf, lpivo, cpivo)
    return dataframe

print(simplex(df))