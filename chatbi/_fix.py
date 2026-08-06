with open('D:/OpenCode-Project/aiagent/chatbi/import_stock_data.py','rb') as f:
    data = f.read()
old = "cols_names = ', '.join('' + h + '' for h in headers)"
new = ('cols_names = ', '.join(` + h + ` for h in headers)')
data = data.replace(old, new)
with open('D:/OpenCode-Project/aiagent/chatbi/import_stock_data.py','wb') as f:
    f.write(data)
print('Done')
