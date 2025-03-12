# -*- coding: utf-8 -*-
# Author: Soltani Charif <https://www.linkedin.com/in/soltani-charif-b0351811a/>

import io
from PyPDF2 import PdfFileWriter, PdfFileReader

from odoo import models


def chunks(lst, size):
    """Yield successive n-sized chunks from list lst."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _merge_splited_pdf_contents(self, pdf_contents):
        """ contact result of pdf_contents in one single pdf_contents"""
        writer = PdfFileWriter()
        streams_to_merge = []
        for pdf_content in pdf_contents:
            stream = io.BytesIO(pdf_content)
            reader = PdfFileReader(stream)
            writer.appendPagesFromReader(reader)
            streams_to_merge.append(stream)
        result_stream = io.BytesIO()
        writer.write(result_stream)
        # we need to return byte content
        final_pdf_content = result_stream.getvalue()
        # close stream after generating the new content
        for stream in streams_to_merge:
            stream.close()
        return final_pdf_content

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """
        The IDEA is simple instead of passing all records to `_render_qweb_pdf` witch will lead to error if the number
        of records is large we pass by batches, and we merge the result of this multiple calls to one single result.
        """
        MAX_LEN_FILES = int(self.env['ir.config_parameter'].sudo().get_param('base.wkhtmltopdf_max_files', 20))

        if 'ledger' in report_ref or 'trial' in report_ref:
            # bypass ledger and trial reports as they give errors as res_ids does not create a page per doc
            # TODO: Find a smart way to check such type of reports
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

        if res_ids and len(res_ids) < MAX_LEN_FILES:
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

        pdf_contents = []
        for _sub_res_ids in chunks(res_ids, MAX_LEN_FILES):
            pdf_content, _ = super()._render_qweb_pdf(report_ref, res_ids=_sub_res_ids, data=data)
            pdf_contents.append(pdf_content)

        return self._merge_splited_pdf_contents(pdf_contents), 'pdf'