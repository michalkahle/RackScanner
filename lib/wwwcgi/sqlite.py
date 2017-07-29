import os, shutil, sys, logging
import wwwcgi

#import cgi
#import cgitb
#cgitb.enable()

version='0.2'

class sqlite(wwwcgi.cgibase):
    def __init__(self):
        wwwcgi.cgibase.__init__(self)
        self.sqlitecmd = 'sqlite3'
        self.sql_tables = '' # list of sql_tables in the database
        self.sql_table = '' # active sql_table
        self.sql_db = 'sqlite.db'
        self.logs = []
        
    def log(self, ll, msg):
        #print '<h1 style="color: red;">', msg, '</h1>'
        self.logs.append(msg)
        
    def printLogs(self):
        print '<br />'.join(self.logs)
        
    def printTableHiddenInputs(self):
        print '<input type="hidden" name="sql_db" value="%s" />' % self.sql_db
        print '<input type="hidden" name="sql_tables" value="%s" />' % self.sql_tables
        print '<input type="hidden" name="sql_table" value="%s" />' % self.sql_table
    
    def printTableHeadRow(self, names):
        l = []
        for n in names:
            l.append('<th>%s</th>' % n)
        print '<tr>' + ''.join(l) + '</tr>'
        
    def printTableInsertRow(self, names):
        l = []
        for n in names:
            l.append('<td><input type="text" name="%s" /></td>' % n)
        print '<tr>' + ''.join(l) + '</tr>'

    def printTable(self, output):
        names, types = self.getFldDefs(self.sql_table)    
        print '<form>'
        self.printTableHiddenInputs()
        print '<input type="submit" name="sql_action" value="Insert" />'       
        print '<table border="1">'
        
        self.printTableHeadRow(names)
        self.printTableInsertRow(names)            
                    
        for line in output:      
            if line.strip():
                print '<tr>'
                for f in line.split('|'):
                    if not f:
                        f = '&nbsp;'
                    print '<td>' + f + '</td>'
                print '</tr>'                     
        print '</table>' 
        print '</form>'
    
    def printOutput(self, output):
        if not output:
            return
            
        if self.sql_sql.upper().strip().find('SELECT') == 0:
            self.printTable(output)
            return
        
        print '<table border="1">'           
        for line in output:      
            print '<tr>'
            for f in line.split('|'):
                print '<td>' + f + '</td>'
            print '</tr>'                      
        print '</table>'
        
    def printErrors(self, errors):
        if errors:
            print 'Messages:<ul>'
            for er in errors:
                print '<li>' + er + '</li>'
            print '</ul>'
            
    def getFldDefs(self, table):
        """ Returns tuple of lists - (fieldnames, fieldtypes)"""
        output, errors = self.execute('.schema ' + table)
        if not output:
            return None
        p = output[0].split('(')
        flds = [f.strip() for f in '('.join(p[1:]).split(',')]
        flds[-1] = flds[-1][:-2]
        names = []
        types = []
        for fld in flds:
            p = fld.strip().split(' ')
            names.append(p[0])
            types.append(' '.join(p[1:]))
        return names, types
        
    def __getitem__(self, attr):
        if hasattr(self, attr):
            return eval('self.' + attr)
    
    def runcmd(self, cmdline):
        self.lastcmdline = cmdline
        cin, cout, cer = os.popen3(cmdline, 'b')
        cin.close()      
        output = cout.readlines()
        errors = cer.readlines()
        cer.close()
        r = cout.close()
        if r:
            print 'close result:' + str(r)            
        return output, errors

    def execute(self, qry):
        out, err = self.runcmd(self.sqlitecmd + ' ' + self.sql_db + ' "' + qry + '"')
        self.log(logging.DEBUG, qry + ' OUTPUT:' + '|'.join(out) + ' ERROR:' 
          + '|'.join(err))
        return out, err
        
    def urlfrm(self):
        return  'sqlite.py?sql_db=%(sql_db)s&sql_sql=%(sql_sql)s&sql_tables=%(sql_tables)s&sql_table=%(sql_table)s'

    def geturl(self, name, value):
        ovalue = getattr(self, name)
        setattr(self, name, value)
        link = self.urlfrm() % self
        setattr(self, name, ovalue)
        return link
        
    def getlink(self, name, value, caption):
        return '<a href="%s">%s</a>' % (self.geturl(name, value), caption)
    
    def printSQLForm(self):
        print '<form name="form" action="sqlite.py">'
        print '<div>Database</div>'
        print '<input name="sql_db" value="%s" /><br />' % self.sql_db
        print '<input type="hidden" name="sql_tables" value="%s" />' % self.sql_tables
        print '<div>sql_sql Query</div>'
        print '<textarea cols=60 rows=4 name="sql_sql">%s</textarea><br />' % self.sql_sql
        print '<input type="submit" name="submit" value="Submit" /><br />'
        print '</form>'

    def printInTagHead(self):
        """ Called between printing <head> and </head>"""
        print """<style>
#contentleftcol { padding: 0.5em; margin: 0.5em; border: solid thin;}        
#contentleftcol li { margin: 0.5em; padding: 0em; }
#contentleftcol ul { margin: 0em; padding: 0em; }
#contentmaincol { margin: 0.5em; padding: 0.5em; }
</style>"""

    def printContentLeftCol(self):
        print '<td id="contentleftcol" valign="top">Tables<br />'
        if not self.sql_tables:
            o, e = self.execute('.tables')
            if o:
                self.sql_tables = ','.join([l.strip() for l in o])
        print '<ul>'
        otable = self.sql_table
        osql = self.sql_sql
        try:
            linefrm = '<a href="' + self.urlfrm() + '">%(sql_table)s</a>'
            for self.sql_table in self.sql_tables.split(','):
                self.sql_sql = 'select * from ' + self.sql_table
                print '<li>' + linefrm % self
                if self.sql_table == otable:
                    print '<br />' + self.getlink('sql_sql','.schema '+otable, 'schema')
                print '</li>'
                
        finally:
          self.sql_table = otable
          self.sql_sql = osql
        print '</ul>'
        
        print '</td>'
          
    def printContentHead(self):
        print '<table><tr>'
        self.printContentLeftCol()
        print '<td id="contentmaincol">'
        osql = self.sql_sql
        self.sql_sql = '.help'
        try:
            print '<a href="' + self.urlfrm() % self + '">Help</a>'
        finally:
            self.sql_sql = osql

    def printContentFoot(self):
        print '</td></tr></sql_table>'
        
    def handleAction(self):
        if not self.sql_action:
            self.log(logging.DEBUG, 'no action')
            return
        if self.sql_action == 'Insert':
            self.handleActionInsert()
            
    def handleActionInsert(self):
        self.log(logging.DEBUG, 'handleActionInsert begin')
        names, types = self.getFldDefs(self.sql_table)
        vals = []
        for name in names:
            vals.append(self.form.getfirst(name, ''))
        qry = ('insert into ' + self.sql_table + ' (' +
          ', '.join(names) + ') values (' + ', '.join(["'%s'" % v for v in vals]) + ');')
        #qry = 'insert into %(table'
        self.log(logging.DEBUG, qry)
        self.execute(qry)
            
    def begin(self):
        self.sql_sql = self.form.getfirst('sql_sql','.help')
        self.sql_db = self.form.getfirst('sql_db','sqlite.db')
        self.sql_tables = self.form.getfirst('sql_tables','')
        self.sql_table = self.form.getfirst('sql_table','')
        self.sql_action = self.form.getfirst('sql_action', '')
        self.log(logging.DEBUG,'Action=' + self.sql_action)
        self.handleAction()
        
    def printContent(self):
        self.printContentHead()        
        self.printSQLForm()

        #print str(self.getFldDefs('test'))
        
        if self.sql_sql:
            #self.printOutputAndErrors;
            print '<div>Result</div>'
            output, errors = self.execute(self.sql_sql)
            print 'Executed command line:</br>' + self.lastcmdline + '<br />' 
            self.printOutput(output)
            self.printErrors(errors)
        self.printLogs()
            
        self.printContentFoot()    


if __name__ == '__main__':
    sqlite().run()
