import os
from pathlib import Path
import shutil
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import MarkdownExporter, PDFExporter


class MetaExecutePreprocessor(ExecutePreprocessor):

    def preprocess_cell(self, cell, resources, cell_index):
        cell, resources = super().preprocess_cell(cell, resources, cell_index)
        # maybe use tags later
        tags = cell['metadata'].get('tags', [])
            
        outputs = cell.get('outputs', [])
        for output in outputs:
            if 'data' in output:
                if 'image/png' in output['data']:
                    if output['output_type'] == 'execute_result':
                        output['output_type'] = 'display_data'
                        del output['execution_count']
        return cell, resources

class Converter:

    KINDS = ['pdf', 'md']
    DATA_DISPLAY_PRIORITY = ['image/png', 'text/html', 'application/pdf', 'text/latex', 
                             'image/svg+xml', 'image/jpeg', 'text/markdown', 'text/plain']

    def __init__(self, path, to, max_rows, max_cols, ss_width, ss_height, resize, chrome_path, limit):
        self.path = path
        self.max_rows = max_rows
        self.max_cols = max_cols
        self.ss_width = ss_width
        self.ss_height = ss_height
        self.resize = resize
        self.chrome_path = chrome_path

        self.nb_home = path.parent
        self.nb_name = path.stem
        self.to = self.get_to(to)
        self.nb = self.get_notebook(limit)
        
    def get_to(self, to):
        if isinstance(to, str):
            to = [to]
        elif not isinstance(to, list):
            raise TypeError('`to` must either be a string or a list. '
                            'Possible values are "pdf" and "md"')

        for kind in to:
            if kind not in self.KINDS:
                raise TypeError('`to` must either be a string or a list. '
                                'Possible values are "pdf" and "md" and not {kind}')
        return to

    def get_notebook(self, limit):
        with open(self.path) as f:
            nb = nbformat.read(f, as_version=4)

        if isinstance(limit, int):
            nb['cells'] = nb['cells'][:limit]

        return nb

    def execute_notebook(self):
        code = 'import pandas as pd;'\
               'from dataframe_image.image_maker import png_maker;'\
              f'pd.DataFrame._repr_png_ = png_maker(max_rows={self.max_rows}, '\
              f'max_cols={self.max_cols}, ss_width={self.ss_width}, '\
              f'ss_height={self.ss_height}, resize={self.resize}, '\
              f'chrome_path={self.chrome_path});'\
               'del png_maker'
        extra_arguments = [f"--InteractiveShellApp.code_to_run='{code}'"]
        resources = {'metadata': {'path': self.nb_home}}
        ep = MetaExecutePreprocessor(timeout=600, kernel_name='python3', allow_errors=True, 
                                    extra_arguments=extra_arguments)
        with open('/Users/Ted/Desktop/log.txt', 'w') as f:
            f.write('adfasd')
        ep.preprocess(self.nb, resources)

    def to_pdf(self):
        pdf = PDFExporter(config={'NbConvertBase': {'display_data_priority': self.DATA_DISPLAY_PRIORITY}})
        resources = resources={'metadata':{'path': str(self.nb_home)}}
        pdf_data, _ = pdf.from_notebook_node(self.nb, resources)
        fn = self.path.with_suffix('.pdf')
        with open(fn, mode='wb') as f:
            f.write(pdf_data)

    def to_md(self):
        images_home = self.nb_home.joinpath('images_from_dataframe_image')
        if images_home.is_dir():
            shutil.rmtree(images_home)
        images_home.mkdir()

        resources = {'metadata': {'path': str(self.nb_home)}, 
                     'output_files_dir': str(images_home)}

        me = MarkdownExporter(config={'NbConvertBase': {'display_data_priority': self.DATA_DISPLAY_PRIORITY}})
        md_data, output_resources = me.from_notebook_node(self.nb, resources)

        # the base64 encoded binary files are saved in output_resources
        for filename, data in output_resources['outputs'].items():
            with open(filename, 'wb') as f:
                f.write(data)
        fn = self.path.with_suffix('.md')
        with open(fn, mode='w') as f:
            f.write(md_data)
                
    def convert(self):
        self.execute_notebook()
        for kind in self.to:
            getattr(self, f'to_{kind}')()

def convert(filename, to='pdf', max_rows=30, max_cols=10, ss_width=1000, 
            ss_height=900, resize=1, chrome_path=None, limit=None):
    '''
    Convert a Jupyter Notebook to pdf or markdown
    '''
    c = Converter(Path(filename), to, max_rows, max_cols, ss_width, ss_height, resize, chrome_path, limit)
    c.convert()
