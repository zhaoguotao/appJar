import sys
sys.path.append("../")

LABS = {'view':'Table View', 'run':'Run SQL', 'log':'Log'}
DB = 'demoDb.sqlite'

import time, sqlite3
from appJar import gui

sqlUpdate = False
numChanges = 0

def checkUpdates():
    global sqlUpdate
    if sqlUpdate:
        app.refreshDbTable(LABS['view'])
        app.refreshDbOptionBox(LABS['view'])
        sqlUpdate = False

def toolbar(btn):
    global numChanges, sqlUpdate
    if btn == 'HOME':
        app.setTabbedFrameSelectedTab('tabs', LABS['view'])
    elif btn == 'LOG':
        app.setTabbedFrameSelectedTab('tabs', LABS['log'])
    elif btn == "COMMIT":
        if numChanges != conn.total_changes:
            conn.commit()
            sqlUpdate = True
            numChanges = conn.total_changes
            app.status(conn.total_changes - numChanges)
            app.setToolbarButtonDisabled("ROLLBACK")
            app.setToolbarButtonDisabled("COMMIT")
        else:
            app.bell()
    elif btn == "ROLLBACK":
        if numChanges != conn.total_changes:
            conn.rollback()
            numChanges = conn.total_changes
            app.status(conn.total_changes - numChanges)
            app.setToolbarButtonDisabled("ROLLBACK")
            app.setToolbarButtonDisabled("COMMIT")
        else:
            app.bell()

def checkChanges():
    if numChanges != conn.total_changes:
        return app.okBox("Discard Changes?", "Press OK to exit and lose changes.")
    else:
        return True

def setFocus(tf):
    global sqlUpdate
    tab = app.getTabbedFrameSelectedTab(tf)
    log("Tab changed to " + tab)
    if tab == LABS['run']:
        app.after(100, app.setTextAreaFocus, LABS['run'])
    elif tab == LABS['view']:
        pass

def updateTable(tbl):
    app.replaceDbTable(LABS['view'], DB, app.option(LABS['view']))

def tableModified(ppp=None):
    print("Changed", ppp)

def log(msg):
    d = time.strftime('%a %H:%M:%S') + ": "
    app.text(LABS['log'], d + msg+"\n")
    app.textAreaTagPattern(LABS["log"], "date", d)

def loadSQL(btn):
    if btn == "Create":
        app.text(LABS['run'], "CREATE TABLE " + app.option(LABS['view']) + " (col type, col type)", replace=True, focus=True)
    elif btn == "Update":
        app.text(LABS['run'], "ALTER TABLE " + app.option(LABS['view']) + " ADD COLUMN 'col' type", replace=True, focus=True)
    elif btn == "Insert":
        app.text(LABS['run'], "INSERT INTO " + app.option(LABS['view']) + " (cols) VALUES (vals)", replace=True, focus=True)
    elif btn == "Delete":
        app.text(LABS['run'], "DELETE FROM " + app.option(LABS['view']) + " WHERE col='val'", replace=True, focus=True)
    elif btn == "Select":
        app.text(LABS['run'], "SELECT * FROM " + app.option(LABS['view']), replace=True, focus=True)

def runSQL(action):
    global sqlUpdate
    if action == "Clear":
        app.text(LABS['run'], replace=True)
        app.message(LABS['run'], '', bg='grey')
        log("SQL cleared")
    elif action == 'Run':
        app.message(LABS['run'], "")
        sql = app.text(LABS['run']).strip()
        if len(sql) > 0:
            try:
                cur = conn.cursor()
                success = cur.execute(sql)
                log("Run SQL - " + sql)
                data = cur.fetchall()
                if not success:
                    app.message(LABS['run'], "Query failed", bg='red')
                else:
                    if len(data) == 0:
                        app.message(LABS['run'], "No rows returned", bg='orange')
                    else:
                        app.message(LABS['run'], data, bg='green')
                    sqlUpdate = True
                app.status(conn.total_changes - numChanges)
                app.setToolbarButtonDisabled("ROLLBACK", False)
                app.setToolbarButtonDisabled("COMMIT", False)
            except sqlite3.OperationalError as e:
                app.bell()
                app.message(LABS['run'], str(e), bg='red')
                log(str(e))
        else:
            app.message(LABS['run'], '', bg='grey')
    app.text(LABS['run'], focus=True)

conn = sqlite3.connect(DB)
with gui("DB Editor", '400x400', bg='red') as app:
    # set up toolbar
    app.toolbar(['HOME', 'COMMIT', 'ROLLBACK', 'LOG'], toolbar, icons=True)
    app.setToolbarIcon("ROLLBACK", 'database-reload')
    app.setToolbarIcon("COMMIT", 'database-upload')
    app.setToolbarIcon("HOME", 'database')
    app.setToolbarIcon("LOG", 'list-unordered')
    app.setToolbarButtonDisabled("ROLLBACK")
    app.setToolbarButtonDisabled("COMMIT")
    # set up statusbar
    app.status(header="Data Changes:", text='0')

    with app.tabbedFrame("tabs", change=setFocus):
        with app.tab(LABS['view']):
            app.addDbOptionBox(LABS['view'], DB, sticky='ne', stretch='column', change=updateTable)
            app.table(LABS['view'], DB, app.option(LABS['view']), kind='db', sticky='news', stretch='both', showMenu=True, change=tableModified)

        with app.tab(LABS['run']):
            app.label(LABS['run'], sticky='new', stretch='column')
            app.text(LABS['run'], sticky='news', stretch='both')
            app.message(LABS['run'], '', bg='grey', border=2, width=400)
            app.buttons(["Create", "Update", "Insert", "Delete", "Select"], loadSQL, stretch='column', sticky='sew', fill=True)
            app.buttons(["Run", "Clear"], runSQL, fill=True)

        with app.tab(LABS['log']):
            app.text(LABS['log'], disabled=True, tags=[['date', {'foreground':'blue', 'background':'yellow'}]])

    app.setStopFunction(checkChanges)
    app.registerEvent(checkUpdates)
conn.close()