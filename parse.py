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
def extract_patterns(text):
    if isinstance(text, str):
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+)，压力(\d+\.\d+)，止损(\d+\.\d+)'
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)，(止损(\d+\.\d+|\d+))?'
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)，止损(\d+\.\d+|\d+)。?' # good
        # pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)(?:（.*?）)?，止损(\d+\.\d+|\d+)'
        # pattern2 = r'([A-Z]+) 支撑(\d+\.\d+|\d+)，压力(\d+\.\d+|\d+)。?'
        pattern = r'([A-Z]+) 支撑(\d+\.\d+|\d+)(?:（.*?）)?，压力(\d+\.\d+|\d+)(?:（.*?）)?，止损(\d+\.\d+|\d+)(?:（.*?）)?'
        matches = re.findall(pattern, text)
        return matches
    return None

def format_currency(x):
    return "${:,.2f}".format(x)

if __name__ == '__main__':
    # client = MyClient()
    # client.run(TOKEN)

    df = pd.read_excel(filePath)
    df['extracted'] = df['Content'].apply(extract_patterns)
    df = df[df['extracted'].apply(lambda x: x != [])]
    df = df[df['extracted'].notna()]
    df = df.explode('extracted').reset_index(drop=True)
    df[['Symbol', 'LimitPrice', 'TakeProfit', 'StopLoss']] = pd.DataFrame(df['extracted'].tolist(), index=df.index)
    df['LotID'] = df.groupby('Date').cumcount() + 1
    df['LotID'] = df['LotID'].astype(object)
    df.loc[df.duplicated(subset=['Date'], keep=False) == False, 'LotID'] = ''

    targetHeader = ["Index", "Timestamp", "Symbol", "Action", "LotID", "Amount", "Quantity", "LimitPrice", "TakeProfit", "StopLoss", "Ready"]
    targetDataFrame = pd.DataFrame(columns=targetHeader)
    targetDataFrame['Timestamp'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')
    targetDataFrame['Symbol'] = df['Symbol']
    targetDataFrame['Action'] = 'TRADE'
    targetDataFrame['LotID'] = df['LotID']
    targetDataFrame['Amount'] = 100_000 / targetDataFrame.groupby('Timestamp')['Timestamp'].transform('count')
    targetDataFrame['Amount'] = targetDataFrame['Amount'].astype(float).apply(lambda x: '${:,.0f}'.format(x))
    targetDataFrame['LimitPrice'] = df['LimitPrice'].astype(float)
    targetDataFrame['TakeProfit'] = df['TakeProfit'].astype(float)
    targetDataFrame['StopLoss'] = df['StopLoss'].astype(float)
    targetDataFrame['Ready'] = 'YES'
    targetDataFrame['Index'] = pd.RangeIndex(start=1, stop=len(df) + 1, step=1)

    targetDataFrame.to_excel('result.xlsx', index=False)
    targetDataFrame.to_csv('result.csv', index=False)
    print('Done')
