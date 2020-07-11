'''
***TABLE users***
userid +++++ updatehr

***TABLE +owner+***
nums +++++ stocks     +++++ porthora
1    ----- null       ----- R$0,00
2    ----- null       ----- 10:25
null ----- [carteira] ----- null

***TABLE stocks***
idxid   +++++ liststock   +++++ dia
[small] ----- [smalllist] ----- [dia]
'''

import sqlite3

#ciro: como comentei no wpp, django rest vai ser uma opção interessante pra você
#eu vi que você criou index: você não lida apenas com dados diários? o ganho pra pouco volume é pequeno
#quando escrever query, usar string format mesmo (o template string, não sei o melhor termo pra isso)
#concatenar string pode dar erro se o tipo da variável mudar - você não pode concatenar '123' com 456 (string com int)

class DBHelper:
    def connect(self, owner, dbname):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
        owner = 'a'+str(owner)
        return owner

    def setup(self, owner, dbname):
        owner = self.connect(owner, dbname)
        usertbl = 'CREATE TABLE IF NOT EXISTS users(userid text, updatehr text)'
        ididx = 'CREATE INDEX IF NOT EXISTS idIndex ON users(userid ASC)'
        updidx = 'CREATE INDEX IF NOT EXISTS updIndex ON users(updatehr ASC)'

        tblstmt = 'CREATE TABLE IF NOT EXISTS '+owner+'(nums text, stocks text, porthora text)'
        numidx = 'CREATE INDEX IF NOT EXISTS numIndex ON '+owner+'(nums ASC)'
        stockidx = 'CREATE INDEX IF NOT EXISTS stockIndex ON '+owner+'(stocks ASC)'
        porhridx = 'CREATE INDEX IF NOT EXISTS porhrIndex ON '+owner+'(porthora ASC)'
        
        stcksstmt = 'CREATE TABLE IF NOT EXISTS stocks(idxid text UNIQUE, liststck text, dia text, )'
        idxidx = 'CREATE INDEX IF NOT EXISTS idxIndex ON stocks(idxid ASC)'
        liststcksidx = 'CREATE INDEX IF NOT EXISTS stckIndex ON stocks(liststck ASC)'
        diaidx = 'CREATE INDEX IF NOT EXISTS dayIndex ON stocks(dia ASC)'
        
        self.conn.execute(usertbl)
        self.conn.execute(ididx)
        self.conn.execute(updidx)

        self.conn.execute(tblstmt)
        self.conn.execute(numidx)
        self.conn.execute(stockidx)
        self.conn.execute(porhridx)
        
        self.conn.execute(stcksstmt)
        self.conn.execute(idxidx)
        self.conn.execute(liststcksidx)
        self.conn.execute(diaidx)
        
        userstmt = 'INSERT INTO users (userid, updatehr) VALUES ("'+owner+'", 0)'

        portstmt = 'INSERT INTO '+owner+' (nums, porthora) VALUES (1, 0)'
        hrstmt = 'INSERT INTO '+owner+' (nums, porthora) VALUES (2, "08:00")'
        
        smallstmt = 'INSERT OR IGNORE INTO stocks (idxid) VALUES ("SMALL")'
        midstmt = 'INSERT OR IGNORE INTO stocks (idxid) VALUES ("MID")'
        
        self.conn.execute(userstmt)

        self.conn.execute(portstmt)
        self.conn.execute(hrstmt)
        
        self.conn.execute(smallstmt)
        self.conn.execute(midstmt)
        
        self.conn.commit()

    def admin_block(self, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = 'UPDATE users SET updatehr = (2) WHERE userid = ("'+owner+'")'
        self.conn.execute(stmt)
        self.conn.commit()

    def update(self, dbname):
        owner = ''
        owner = self.connect(owner, dbname)
        stmt = 'SELECT * FROM users'
        try:
            #ciro: salvar o resultado da query antes de acessar os dados
            #pra evitar executar a query pra cada iteração
            s = [x for x in self.conn.execute(stmt)]
            return s
        except:
            return False
    
    def update_stop(self, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = 'UPDATE users SET updatehr = (0) WHERE userid = ("'+owner+'")'
        self.conn.execute(stmt)
        self.conn.commit()

    def add_stock(self, item_text, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = 'INSERT OR IGNORE INTO '+owner+' (stocks) VALUES ("'+item_text+'")'
        self.conn.execute(stmt)
        self.conn.commit()

    def delete_stock(self, item_text, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = 'DELETE FROM '+owner+' WHERE stocks = ("'+item_text+'")'
        self.conn.execute(stmt)
        self.conn.commit()

    def get_carteira(self, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = 'SELECT stocks FROM '+owner
        s = [x[0] for x in self.conn.execute(stmt)]
        r = [x for x in s if x != None]
        return r

    def upd_port(self, item_text, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = 'UPDATE '+owner+' SET porthora = ('+item_text+') WHERE nums = (1)'
        self.conn.execute(stmt)
        self.conn.commit()

    def upd_hora(self, item_text, owner, dbname):
        owner = self.connect(owner, dbname)
        updstmt = 'UPDATE users SET updatehr = (1) WHERE userid = ("'+owner+'")'
        hrstmt = 'UPDATE '+owner+' SET porthora = ("'+item_text+'") WHERE nums = (2)'
        self.conn.execute(updstmt)
        self.conn.execute(hrstmt)
        self.conn.commit()

    def upd_stocks(self, item_text, date, dbname):
        owner = self.connect(owner=123, dbname=dbname)
        stmt = 'UPDATE stocks SET liststck = ("'+item_text+'"), dia = ("'+date+'") WHERE idxid = ("SMALL")'
        self.conn.execute(stmt)
        self.conn.commit()

    def get_stocks(self, item_text, dbname):
        owner = self.connect(owner=123, dbname=dbname)
        stmt = 'SELECT liststck, dia FROM stocks WHERE idxid = ("'+item_text+'")'
        r = [x for x in self.conn.execute(stmt)]
        return r

    def get_info(self, owner, dbname):
        owner = self.connect(owner, dbname)
        stmt = ('SELECT porthora FROM '+owner+' ORDER BY CASE WHEN nums IS null THEN 1 ELSE 0 END, nums')
        r = [x[0] for x in self.conn.execute(stmt)]
        return r