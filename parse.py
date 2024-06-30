import os
import pandas as pd
import re

basePath = os.getcwd()
folderName = 'data'
fileName = 'miji_signal_record.xlsx'
filePath = os.path.join(basePath, folderName, fileName)
print("Current Working Directory:", basePath)
print("File Path:", filePath)


# Define a function to extract the patterns
def extract_patterns(text: str, type: int):
    if isinstance(text, str):
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+)，压力(\d+\.\d+)，止损(\d+\.\d+)'
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)，(止损(\d+\.\d+|\d+))?'
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)，止损(\d+\.\d+|\d+)。?' # good
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)(?:（.*?）)?，止损(\d+\.\d+|\d+)'
        # pattern2 = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)。?'
        if type == 1:
            pattern = r'([A-Z]+)支撑(\d+\.\d+|\d+)(?:（.*?）)?，压力(\d+\.\d+|\d+)(?:（.*?）)?，止损(\d+\.\d+|\d+)(?:（.*?）)?'
            matches = re.findall(pattern, text)
            return matches
        elif type == 2:
            # pattern = r'([A-Z]+)支撑(\d+\.\d+|\d+)(?:（.*?）)?，压力(\d+\.\d+|\d+)(?:（.*?）)?，跌破(\d+\.\d+|\d+)止损(?:（.*?）)?'
            pattern = r'([A-Z]+)支撑(\d+\.\d+|\d+)(?:（.*?）)?，压力(\d+\.\d+|\d+)(?:（.*?）)?，跌破(\d+\.\d+|\d+).*?止损(?:（.*?）)?'
            matches = re.findall(pattern, text)
            return matches
    return None


def format_currency(x):
    return "${:,.2f}".format(x)


def combine_lists(row, columns):
    combinedList = []
    for column in columns:
        if column in row and row[column]:  # Ensure the column exists and is not None
            combinedList.extend(row[column])
    return combinedList


if __name__ == '__main__':
    df = pd.read_excel(filePath)
    df['Content'] = df['Content'].str.replace('@幂蜂群', '', regex=False)
    df['Content'] = df['Content'].str.replace('@deleted-role', '', regex=False)
    df['Content'] = df['Content'].str.replace('@everyone', '', regex=False)
    df['Content'] = df['Content'].str.replace(" ", "", regex=False)
    df['Content'] = df['Content'].str.replace('、', '，', regex=False)
    df = df[df['Content'].notna()]
    df = df.drop(columns=['AuthorID', 'Author', 'Attachments', 'Reactions'])
    types = [1, 2]
    for type in types:
        df['pattern' + str(type)] = df['Content'].apply(lambda x: extract_patterns(x, type))

    columnsToCombine = ['pattern' + str(type) for type in types]
    df['signal'] = df.apply(combine_lists, axis=1, args=(columnsToCombine,))
    df = df[df['signal'].apply(lambda x: x != [])]
    df = df[df['signal'].notna()]
    df = df.explode('signal').reset_index(drop=True)
    df[['Symbol', 'LimitPrice', 'TakeProfit', 'StopLoss']] = pd.DataFrame(df['signal'].tolist(), index=df.index)
    # df['LotID'] = df.groupby('Date').cumcount() + 1
    # df['LotID'] = df['LotID'].astype(object)
    df.loc[df.duplicated(subset=['Date'], keep=False) == False, 'LotID'] = ''

    # Prepare target dataframe
    targetHeader = ["Index", "Timestamp", "Symbol", "Action", "LotID", "Amount", "Quantity", "LimitPrice", "TakeProfit", "StopLoss", "Ready"]
    targetDataFrame = pd.DataFrame(columns=targetHeader)
    targetDataFrame['Timestamp'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')
    targetDataFrame['Symbol'] = df['Symbol']
    targetDataFrame['Action'] = 'TRADE'
    # targetDataFrame['LotID'] = df['LotID']
    # targetDataFrame['Amount'] = 100_000 / targetDataFrame.groupby('Timestamp')['Timestamp'].transform('count')
    targetDataFrame['Amount'] = 100_000
    targetDataFrame['Amount'] = targetDataFrame['Amount'].astype(float).apply(lambda x: '${:,.0f}'.format(x))
    targetDataFrame['LimitPrice'] = df['LimitPrice'].astype(float)
    targetDataFrame['TakeProfit'] = df['TakeProfit'].astype(float)
    targetDataFrame['StopLoss'] = df['StopLoss'].astype(float)
    targetDataFrame['Ready'] = 'YES'
    targetDataFrame['Index'] = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)

    targetDataFrame.to_excel('resultTest.xlsx', index=False)
    targetDataFrame.to_csv('resultTest.csv', index=False)
    print('Done')
