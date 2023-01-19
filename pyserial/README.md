# UART toolchain

## UART communication

## Logfile parsing

To parse the log from our tool, you can use the following commands

```
python3 -m pyserial.raw2csv serial_1123_1048.txt
```

You will see the following result

```
4649 lines read
930 lines data
Invalid interval 21  (@21   )
     pixel00   pixel01   pixel02   pixel03  ...   pixel21   pixel22   pixel23   pixel24
0   00000000  047e8510  049025c9  0491d298  ...  0452fdb1  043bd353  043bd353  10101010
1   048ddb08  047ecce1  0490c472  04924b7c  ...  04533939  043b89dc  043b89dc  10101010
...
34  048d1131  047e0a78  048fffa2  0491cbc3  ...  04535cb1  043b6a9b  043b6a9b  10101010
35  00000000  047d5fd9  04ef4fdd  04915099  ...  04d3ad3f  043b5611  043b5611  10101010

[36 rows x 25 columns]
Export serial_1123_1048.csv
Export serial_1123_1048_time.csv

```

And two files ```serial_1123_1048.csv``` and ```serial_1123_1048_time.csv```. You can use our [visualization tools](https://git.ece.cmu.edu/chingyil/capsensor-microcontroller/-/tree/master/visualization).
