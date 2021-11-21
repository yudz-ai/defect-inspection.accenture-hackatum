import pyodbc
server = 'dago-ai-database.database.windows.net'
database = 'customaidatabase'
username = 'dagoai'
password = '{AIDatabase1!}'   
driver= '{ODBC Driver 17 for SQL Server}'

with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
    with conn.cursor() as cursor:
        # cursor.execute("SELECT * FROM [dbo].[DetectionData]")
        cursor.execute("INSERT INTO [dbo].[DetectionData] ([TypeStr],[Result]) VALUES ('other2',1)")
        conn.commit()
        # row = cursor.fetchone()
        # while row:
        #     print (str(row[0]) + " " + str(row[1]))
        #     row = cursor.fetchone()

