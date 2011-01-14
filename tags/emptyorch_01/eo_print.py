from wx.html import HtmlEasyPrinting
from wx import Printout, PrintData, PAPER_LETTER, PrintDialogData
from wx import Printer as wxPrinter, MessageBox, PrintPreview, PrintDialog

class SongPrinter(HtmlEasyPrinting):
    def __init__(self):
        HtmlEasyPrinting.__init__(self)

    def GetHtmlText(self, data):
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

        #datalen = len(data)
        #for i in range(0, datalen, numrows):
        #    print i
        #    html_text = "%s%s" % (html_text, "<tr>")
        #    subtable = self.SongSubTable(
        #        data[i:min(datalen-1,i+numrows)]
        #    )
        #    html_text = "%s<td>%s</td>" % (
        #        html_text,
        #        subtable,
        #    )
        #    html_text = "%s</tr>" % html_text
        #html_text = "%s</table>" % html_text
        return html_text

    def SongSubTable(self, data):
    #def GetHtmlText(self, data):
        html_text = """
            <table border='1'>
            <tr>
            <th>Artist</th>
            <th>Song</th>
            <th>Artist</th>
            <th>Song</th>
            </tr>
        """
        datalen = len(data)
        for i in range(0, datalen, 2):
        #for row in data:
            row0 = data[i]
            row1 = ('','')
            if i < (datalen-1):
                row1 = data[i+1]
            rowdata = """
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            """ % (
                row0[0],
                row0[1],
                row1[0],
                row1[1]
            )
            html_text = "%s<tr>%s</tr>" % (
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

if __name__ == "__main__":
    somedata = """ This is
a sample Document!!

Wee

Yay
"""
    p = Printer()

    p.PreviewText(somedata, "FOO!")
