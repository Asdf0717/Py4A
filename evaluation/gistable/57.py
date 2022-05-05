#!/usr/bin/env python
import re
from urllib.request import urlopen

# Get the webpage's source html code
source = 'http://www.goodinfo.tw/stockinfo/StockDividendSchedule.asp?STOCK_ID='
ID = '2002'
filename = ID+'.html'
result = urlopen(source+ID).read().decode("big5")#.encode("utf8")

# Get the data <table></table>
regex = re.compile("<table class='std_tbl' width='100%'.*<\/table>")
datatable = regex.findall(result)[0]

# Get the data row <tr></tr>
regex = re.compile("<tr bgcolor=.*</tr>")
datarow = regex.findall(datatable)
string = datarow[0].strip()

# Clean data row
cleanlist = ["<nobr>", " align='right'", "</nobr>"]
for target in cleanlist:
    string = string.replace(target,'').strip(' ')
# Special operation on empty data cell
string = string.replace("</td>"," ")
    
# Get each data <td></td>
datalist = string.split('</tr>')
totaldata = {}
infolist =['盈餘所屬年度',
           '股利發放年度',
           '股東會日期',
           '除息交易日',
           '除息參考價（元）',
           '除權交易日',
           '除權參考價（元）',
           '股利發放年度之股價統計：最高',
           '股利發放年度之股價統計：最低',
           '股利發放年度之股價統計：年均',
           '現金股利：盈餘',
           '現金股利：公積',
           '現金股利：合計',
           '股票股利：盈餘',
           '股票股利：公積',
           '股票股利：合計',
           '股利合計',
           '年均殖利率（%）']

# Print Out the result
data_dict = {}
for item in datalist[:-1]:
    if '股' in item or '權' in item:
        continue
    rowlist = item.split('<td>')[1:]
    newrowlist = {}
    for num,item in enumerate(rowlist):
        newrowlist[infolist[num]] = item.strip()
        print(infolist[num],'---',item.strip())
    print('=========')
    data_dict[rowlist[1].strip()] = newrowlist
    
print(data_dict)