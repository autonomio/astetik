def toggle():

    from IPython.display import HTML

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

    import warnings
    warnings.filterwarnings('ignore')
