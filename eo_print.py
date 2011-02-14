import types

from wx.html import HtmlEasyPrinting
from wx import Printout, PrintData, PAPER_LETTER, PrintDialogData
from wx import Printer as wxPrinter, MessageBox, PrintPreview, PrintDialog
#import  wx.lib.printout as  printout
from wx.lib.printout import PrintTable, PrintTableDraw

class NewPrinter():
    def __init__(self, frame):
        self.frame = frame

    def Preview(self, data):
        data.sort(lambda a, b: cmp(a[0].lower(), b[0].lower()))
        new_data = []
        for val in data:
            new_data.append([val[0], val[1]])

        header = ['artist', 'song'] 

        prt = EOPrintTable(self.frame)
        prt.data = new_data
        prt.set_column = [1,1]
        prt.label = header
        prt.num_regions = 3
        prt.SetHeader("Song Printout")
        prt.SetFooter("Page No", type="Num")
        prt.Preview()


class SongPrinter(HtmlEasyPrinting):
    def __init__(self):
        HtmlEasyPrinting.__init__(self)

    def _GetHtmlText(self, data):
        numrows = 64 
        html_text = ""
        data.sort(lambda a, b: cmp(a[0].lower(), b[0].lower()))
        
        artist = ""
        for row in data:
            if artist.lower() != row[0].lower():
                artist = row[0]
                html_text = "%s<br><b>%s:</b><br>%s" % (
                        html_text,
                        artist,
                        row[1]
                )
            else:
                html_text = ", ".join((
                    html_text,
                    row[1]
                ))
        return html_text

    def GetHtmlText(self, data):
        html_text=""
        numrows = 15
        numsubtables = 2
        data.sort(lambda a, b: cmp(a[0].lower(), b[0].lower()))
        
        artist = ""
        datalen = len(data)
        datalen = 600
        datacount = 0
        while True:
            print datacount
            html_text = "%s<table border='4' width=600, height=800>" % html_text
            html_text = "%s%s" % (html_text, "<tr>")

            for t in range(numsubtables):
                endindex = min(datalen-1, datacount+numrows)
                print "%s to %s" % (datacount, endindex)
                subtable = self.SongSubTable(
                    data[datacount:endindex]
                )
                html_text = "%s<td>%s</td>" % (
                    html_text,
                    subtable,
                )
                datacount+=numrows
            html_text = "%s</tr>" % html_text
            if endindex >= (datalen-1):
                break
            html_text = "%s</table>" % html_text
            html_text = '%s<div style="page-break-before:always"> </div>' % html_text
        return html_text

    def SongSubTable(self, data):
    #def GetHtmlText(self, data):
        html_text = """
            <table border='1' width=300, height=500>
            <tr>
            <th>Artist</th>
            <th>Song</th>
            </tr>
        """
        datalen = len(data)
        #for i in range(0, datalen, 2):
        for row in data:
            rowdata = """
                <td align=left height=20>%s</td>
                <td align=left height=20>%s</td>
            """ % (
                row[0],
                row[1],
            )
            html_text = "%s<tr height=12>%s</tr>" % (
                html_text,
                rowdata
            )
        html_text = "%s</table>" % html_text
        #print self.GetCharWidth()
        #print self.GetCharHeight()
        #print self.GetPageSetupData().GetPaperSize()
        return html_text

    def Print(self, data, doc_name):
        self.SetHeader(doc_name)
        self.PrintText(self.GetHtmlText(data))

    def PreviewText(self, data, doc_name):
        self.SetHeader(doc_name)
        HtmlEasyPrinting.PreviewText(
            self,
            self.GetHtmlText(data)
        )
        
        print self.GetPageSetupData().GetPaperSize()
        #print self.GetPrintData()

#License: MIT
import wx
from wx import Printer as wxPrinter

def GetErrorText():
    "Put your error text logic here.  See Python Cookbook for a useful example of error text."
    return "Some error occurred."

class Printer(wx.Printout):
    def __init__(self, frame, text = "", name = ""):
        "Prepares the Printing object.  Note: change current_y for 1, 1.5, 2 spacing for lines."
        wx.Printout.__init__(self)
        self.printer_config = wx.PrintData()
        self.printer_config.SetPaperId(wx.PAPER_LETTER)
        self.printer_config.SetOrientation(wx.LANDSCAPE)
        self.frame = frame
        self.doc_text = text
        self.doc_name = name
        self.current_y = 15  #y should be either (15, 22, 30)
        if self.current_y == 15:
            self.num_lines_per_page = 50
        elif self.current_y == 22:
            self.num_lines_per_page = 35
        else:
            self.num_lines_per_page = 25


    def Print(self, text, doc_name):
        "Prints the given text.  Currently doc_name logic doesn't exist.  E.g. might be useful for a footer.."
        self.doc_text = text
        self.doc_name = doc_name
        pdd = wx.PrintDialogData()
        pdd.SetPrintData(self.printer_config)
        printer = wxPrinter(pdd)
        if not printer.Print(self.frame,self):
            wx.MessageBox("Unable to print the document.")
        else:
            self.printer_config = printer.GetPrintDialogData().GetPrintData()

    def PreviewText(self, text, doc_name):
        "This function displays the preview window for the text with the given header."
        #try:
        self.doc_name = doc_name
        self.doc_text = text

        #Destructor fix by Peter Milliken -- with change to Printer.__init__()
        print1 = Printer(self.frame, text = self.doc_text, name = self.doc_name)
        print2 = Printer(self.frame, text = self.doc_text, name = self.doc_name)
        preview = wx.PrintPreview(print1, print2, self.printer_config)

        if not preview.Ok():
            wx.MessageBox("Unable to display preview of document.")
            return

        preview_window = wx.PreviewFrame(preview, self.frame, \
                                        "Print Preview - %s" % doc_name)
        preview_window.Initialize()
        preview_window.SetPosition(self.frame.GetPosition())
        preview_window.SetSize(self.frame.GetSize())
        preview_window.MakeModal(True)
        preview_window.Show(True)
        #except:
        #    wx.MessageBox(GetErrorText())

    def PageSetup(self):
        "This function handles displaying the Page Setup window and retrieving the user selected options."
        config_dialog = wx.PageSetupDialog(self.frame)   #replaces PrintDialog
        config_dialog.GetPageSetupData()
        print self.printer_config        
        config_dialog.ShowModal()
        self.printer_config = config_dialog.GetPageSetupData()
        print self.printer_config
        config_dialog.Destroy()

    def OnBeginDocument(self,start,end):
        "Do any end of document logic here."
        wx.Printout.OnBeginDocument(self,start,end)

    def OnEndDocument(self):
        "Do any end of document logic here."
        wx.Printout.OnEndDocument(self)

    def OnBeginPrinting(self):
        "Do printing initialization logic here."
        wx.Printout.OnBeginPrinting(self)

    def OnEndPrinting(self):
        "Do any post printing logic here."
        wx.Printout.OnEndPrinting(self)

    def OnPreparePrinting(self):
        "Do any logic to prepare for printing here."
        wx.Printout.OnPreparePrinting(self)

    def HasPage(self, page_num):
        "This function is called to determine if the specified page exists."
        return len(self.GetPageText(page_num)) > 0

    def GetPageInfo(self):
        """
        This returns the page information: what is the page range available, and what is the selected page range.
        Currently the selected page range is always the available page range.  This logic should be changed if you need
        greater flexibility.
        """

        minPage = 1
        maxPage = int(len(self.doc_text.split('\n'))/self.num_lines_per_page)
        fromPage, toPage = minPage, maxPage
        return (minPage,maxPage,fromPage,toPage)

    def OnPrintPage(self, page_num):
        "This function / event is executed for each page that needs to be printed."
        print "PageNum:", page_num
        dc = self.GetDC()
        x,y = 25, self.current_y
        if not self.IsPreview():
            y *=4
        line_count = 1
        for line in self.GetPageText(page_num):
            dc.DrawText(line, x, y*line_count)
            line_count += 1

        return True

    def GetPageText(self, page_num):
        "This function returns the text to be displayed for the given page number."
        lines = self.doc_text.split('\n')
        lines_for_page = lines[(page_num -1)*self.num_lines_per_page: page_num*(self.num_lines_per_page-1)]
        return lines_for_page

    def PreviewTable(self, data):
        data.sort(lambda a, b: cmp(a[0].lower(), b[0].lower()))
        new_data = []
        for val in data:
            new_data.append([val[0], val[1]])

        header = ['artist', 'song', ''] * 3

        prt = printout.PrintTable(self.frame)
        prt.data = new_data
        prt.set_column = [1, 1, .1, 1, 1, .1, 1, 1, .1]
        prt.label = header
        prt.SetHeader("Song Printout")
        prt.SetFooter("Page No", type="Num")
        prt.Preview()

class EOPrintTableDraw(PrintTableDraw):

    fitcache = {}

    def SetDefaults(self):
        # Number of pages per page
        self.num_regions = self.parent.num_regions
        PrintTableDraw.SetDefaults(self)

    def AdjustValues(self):
        PrintTableDraw.AdjustValues(self)
        self.region_margin = 20
        self.colwidth = self.column[-1] - self.column[0] + self.region_margin
        print "self.column:", self.column
        print "self.column_align:", self.column_align

    def OutCanvas(self):
        print "PrintTableData.OutCanvas"
        self.AdjustValues()
        self.SetPointAdjust()

        self.y_start = self.ptop_margin + self.vertical_offset
        self.y_end = self.parent.page_height * self.pheight - self.pbottom_margin + self.vertical_offset

        self.SetPrintFont(self.label_font)

        x, y = self.DC.GetTextExtent("W")
        self.label_space = y

        self.SetPrintFont(self.text_font)

        x, y = self.DC.GetTextExtent("W")
        self.space = y

        if self.total_pages is None:
            self.GetTotalPages()    # total pages for display/printing

        self.data_cnt = self.page_index[self.page-1] * 3

        self.draw = True
        self.PrintHeader()
        self.PrintFooter()
        for i in range(self.num_regions):
            self.OutPage(i)

    def GetTotalPages(self):
        print "Real Get Total Pages"
        self.data_cnt = 0
        self.draw = False
        self.page_index = [0]

        cnt = 0
        while 1:
            test = self.OutPage()
            self.page_index.append(self.data_cnt)
            if  test == False:
                break
            cnt = cnt + 1

        self.total_pages = cnt + 1
        print "TOTAL:", self.total_pages

    def OutPage(self, regnum=0):
        newpage = True
        self.y = self.y_start
        self.end_x = self.column[-1]

        if self.data_cnt < len(self.data):  # if there data for display on the page
            if self.label != []:        # check if header defined
                self.PrintLabel(regnum)
        else:
            return False


        for i in range(len(self.data)):
            val = self.data[i]
            try:
                row_val = self.data[self.data_cnt]
            except:
                self.FinishDraw(regnum)
                return False

            if not self.fitcache.has_key(i):
                max_y = self.PrintRow(row_val, False, regnum=regnum)       
                # test to see if row will fit in remaining space
                test = max_y + self.space
                if test > self.y_end:
                    fits = False
                else:
                    fits = True
                self.fitcache[i] = fits
            else:
                fits = self.fitcache[i]

            if not fits and not newpage:
                break

            #self.ColourRowCells(max_y-self.y+self.space, regnum)       # colour the row/column
            max_y = self.PrintRow(row_val, True, regnum=regnum)      # row fits - print text
            self.DrawGridLine(regnum)     # top line of cell
            self.y = max_y + self.space

            if self.y > self.y_end:
                break

            self.data_cnt = self.data_cnt + 1
            newpage = False

        self.FinishDraw(regnum)

        if self.data_cnt == len(self.data):    # last value in list
            return False

        return True

    def PrintLabel(self, regnum):
        self.pt_space_before = self.label_pt_space_before   # set the point spacing
        self.pt_space_after = self.label_pt_space_after

        self.LabelColorRow(self.label_colour, regnum)
        self.SetPrintFont(self.label_font)

        self.col = 0
        max_y = 0
        for vtxt in self.label:
            self.region = self.column[self.col+1] - self.column[self.col]
            self.indent = self.column[self.col] + (regnum * self.colwidth)

            self.align = wx.ALIGN_LEFT

            max_out = self.OutTextRegion(vtxt, True)
            if max_out > max_y:
                max_y = max_out
            self.col = self.col + 1

        self.DrawGridLine(regnum)     # top line of label
        self.y = max_y + self.label_space

    def LabelColorRow(self, colour, regnum):
        brush = wx.Brush(colour, wx.SOLID)
        self.DC.SetBrush(brush)
        height = self.label_space + self.label_pt_space_before + self.label_pt_space_after
        start_x = self.column[0] + (regnum * self.colwidth)
        self.DC.DrawRectangle(start_x, self.y,
                              self.end_x-self.column[0]+1, height)

    def ColourRowCells(self, height, regnum):
        if self.draw == False:
            return

        col = 0
        for colour in self.column_bgcolour:
            cellcolour = self.GetCellColour(self.data_cnt, col)
            if cellcolour is not None:
                colour = cellcolour

            brush = wx.Brush(colour, wx.SOLID)
            self.DC.SetBrush(brush)
            self.DC.SetPen(wx.Pen(wx.NamedColour('WHITE'), 0))

            start_x = self.column[col] + (regnum * self.colwidth)
            width = self.column[col+1] - start_x + 2 
            self.DC.DrawRectangle(start_x, self.y, width, height)
            col = col + 1

    def PrintRow(self, row_val, draw = True, align = wx.ALIGN_LEFT, startcol=0, regnum=0):
        self.SetPrintFont(self.text_font)

        self.pt_space_before = self.text_pt_space_before   # set the point spacing
        self.pt_space_after = self.text_pt_space_after

        self.col = 0 
        max_y = 0

        print "-------------"
        print "ROWVAL:", row_val

        for vtxt in row_val:
            if not isinstance(vtxt,types.StringTypes):
                vtxt = str(vtxt)
            self.region = self.column[self.col+1] - self.column[self.col]
            #self.indent = self.column[self.col]
            self.indent = self.column[self.col] + (regnum * self.colwidth)

            print "Self.Col:", self.col
            print "COLWIDTH:", self.colwidth
            print "Regnum:", regnum
            print "Self.Region:", self.region
            print "Self.Indent:", self.indent
            print "vtxt:", vtxt
            print "Draw:", draw
            self.align = self.column_align[self.col]

            fcolour = self.column_txtcolour[self.col]       # set font colour
            celltext = self.GetCellTextColour(self.data_cnt, self.col)
            if celltext is not None:
                fcolour = celltext      # override the column colour

            self.DC.SetTextForeground(fcolour)

            max_out = self.OutTextRegion(vtxt, draw)
            if max_out > max_y:
                max_y = max_out
            self.col = self.col + 1
        return max_y

    def FinishDraw(self, regnum=0):
        self.DrawGridLine(regnum)     # draw last row line
        self.DrawColumns(regnum)      # draw all vertical lines

    def DrawGridLine(self, regnum=0):
        if self.draw == True \
        and len(self.column) > 2:    #supress grid lines if only one column
            try:
                size = self.row_line_size[self.data_cnt]
            except:
                size = self.row_def_line_size

            if size < 1: return

            try:
                colour = self.row_line_colour[self.data_cnt]
            except:
                colour = self.row_def_line_colour

            self.DC.SetPen(wx.Pen(colour, size))

            y_out = self.y
#            y_out = self.y + self.pt_space_before + self.pt_space_after     # adjust for extra spacing
            start_x = self.column[0] + (regnum * self.colwidth)
            end_x = self.end_x + (regnum * self.colwidth)
            self.DC.DrawLine(start_x, y_out, end_x, y_out)

    def DrawColumns(self, regnum=0):
        if self.draw == True \
        and len(self.column) > 2:   #surpress grid line if only one column
            col = 0
            for val in self.column:
                try:
                    size = self.column_line_size[col]
                except:
                    size = self.column_def_line_size

                if size < 1: continue

                try:
                    colour = self.column_line_colour[col]
                except:
                    colour = self.column_def_line_colour

                indent = val + (regnum * self.colwidth)

                self.DC.SetPen(wx.Pen(colour, size))
                self.DC.DrawLine(indent, self.y_start, indent, self.y)
                col = col + 1


class EOPrintTable(PrintTable):
    def __init__(self, *args, **kwds):
        self.num_regions = 1
        PrintTable.__init__(self, *args, **kwds)

    def DoDrawing(self, DC):
        print "self.PrintTable.DoDrawing"
        size = DC.GetSize()
        DC.BeginDrawing()

        table = EOPrintTableDraw(self, DC, size)
        table.data = self.data
        print "Datalen:", len(table.data)
        table.set_column = self.set_column
        table.label = self.label
        table.SetPage(self.page)
        print self.page

        if self.preview is None:
            table.SetPSize(size[0]/self.page_width, size[1]/self.page_height)
            table.SetPTSize(size[0], size[1])
            table.SetPreview(False)
        else:
            if self.preview == 1:
                table.scale = self.scale
                table.SetPSize(size[0]/self.page_width, size[1]/self.page_height)
            else:
                table.SetPSize(self.pwidth, self.pheight)

            table.SetPTSize(self.ptwidth, self.ptheight)
            table.SetPreview(self.preview)

        table.OutCanvas()
        self.page_total = table.total_pages     # total display pages

        DC.EndDrawing()

        self.ymax = DC.MaxY()
        self.xmax = DC.MaxX()

        self.sizeh = size[0]
        self.sizew = size[1]


def testPrinter():
    app = wx.PySimpleApp()
    frame = wx.Frame(None)
    somedata = """ This is
a sample Document!!

Wee

Yay
"""
    p = Printer(frame)

    p.PreviewText(somedata, "FOO!")
    app.MainLoop()

def testPrintTable():
    app = wx.PySimpleApp()
    frame = wx.Frame(None)
    somedata = []
    for i in range(500):
        somedata.append(['foo_%s' % i, 'bar_%s' % i])

    p = NewPrinter(frame)

    p.Preview(somedata)
    app.MainLoop()

if __name__ == "__main__":
    testPrintTable()
