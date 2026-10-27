import tkinter as tk
import customtkinter as ctk


class BarChart(ctk.CTkFrame):
    def __init__(self,parent,title,formatter=str):
        super().__init__(parent,fg_color='white',corner_radius=10)
        self.pack(fill='x',pady=(0,14))
        self.values=[]
        self.bar_values={}
        self.formatter=formatter
        ctk.CTkLabel(self,text=title,text_color='#203F78',font=ctk.CTkFont(size=17,weight='bold')).pack(anchor='w',padx=16,pady=(12,2))
        self.details=ctk.CTkLabel(self,text='Pasa el cursor sobre una barra para ver el detalle.',text_color='#748195')
        self.details.pack(anchor='w',padx=16)
        self.canvas=tk.Canvas(self,height=190,bg='white',highlightthickness=0)
        self.canvas.pack(fill='x',padx=12,pady=10)
        self.canvas.bind('<Configure>',lambda _:self.draw())
        self.canvas.bind('<Motion>',self.hover)

    def hover(self,event):
        current=self.canvas.find_withtag('current')
        if current and current[0] in self.bar_values:
            label,value=self.bar_values[current[0]]
            self.details.configure(text=f'{label}: {self.formatter(value)}')

    def set_values(self,values):
        self.values=values
        self.draw()

    def draw(self):
        c=self.canvas
        c.delete('all')
        self.bar_values={}
        width=max(c.winfo_width(),300)
        nonzero=any(v for _,v in self.values)
        if not nonzero:
            c.create_text(width/2,90,text='Sin movimientos en este periodo',fill='#748195',font=('Segoe UI',12))
            return
        maximum=max(v for _,v in self.values) or 1
        left=90; plot_width=max(width-left-20,100)
        for fraction in (0,.5,1):
            y=150-120*fraction
            c.create_line(left,y,width-12,y,fill='#E2E8F0')
            c.create_text(left-8,y,text=self.formatter(round(maximum*fraction)),anchor='e',fill='#748195',font=('Segoe UI',9))
        step=plot_width/len(self.values)
        label_step=max(1,(len(self.values)+7)//8)
        for index,(label,value) in enumerate(self.values):
            x=left+index*step
            bar=c.create_rectangle(x+1,150-value/maximum*120,x+max(2,step-2),150,fill='#F47724',outline='')
            self.bar_values[bar]=(label,value)
            if index%label_step==0:
                c.create_text(x+step/2,166,text=label,fill='#748195',font=('Segoe UI',9),width=max(step*label_step,60))
