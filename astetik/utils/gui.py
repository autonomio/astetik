import warnings
from IPython.display import HTML

def toggle():

    html = HTML('''<script>
    code_show=true; 
    function code_toggle() {
     if (code_show){
     $('div.input').hide();
     } else {
     $('div.input').show();
     }
     code_show = !code_show
    } 
    $( document ).ready(code_toggle);
    </script>
    <a href="javascript:code_toggle()">toggle code cells</a>''')
    return html

def warning():
    
    warnings.filterwarnings('ignore')