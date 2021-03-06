# pylint: disable=missing-docstring
from resolwe.flow.models import Data
from resolwe.test import tag_process

from resolwe_bio.utils.test import BioProcessTestCase


class ExpressionProcessorTestCase(BioProcessTestCase):

    @tag_process('cufflinks', 'cuffmerge')
    def test_cufflinks(self):
        with self.preparation_stage():
            genome = self.prepare_genome()
            reads = self.prepare_reads()
            annotation = self.prepare_annotation_gff()

            inputs = {
                'genome': genome.pk,
                'reads': reads.pk,
                'annotation': annotation.pk,
                'PE_options': {
                    'library_type': "fr-unstranded"}}
            aligned_reads = self.run_process('alignment-tophat2', inputs)

        inputs = {
            'alignment': aligned_reads.pk,
            'annotation': annotation.pk,
            'genome': genome.pk}
        cuff_exp = self.run_process('cufflinks', inputs)
        self.assertFile(cuff_exp, 'transcripts', 'cufflinks_transcripts.gtf')
        self.assertFields(cuff_exp, 'species', 'Dictyostelium discoideum')
        self.assertFields(cuff_exp, 'build', 'dd-05-2009')

        inputs = {
            'alignment': aligned_reads.pk,
            'annotation': annotation.pk,
            'genome': genome.pk}
        cuff_exp2 = self.run_process('cufflinks', inputs)

        inputs = {
            'expressions': [cuff_exp.pk, cuff_exp2.pk],
            'gff': annotation.pk,
            'genome': genome.pk}
        cuff_merge = self.run_process('cuffmerge', inputs)
        self.assertFile(cuff_merge, 'annot', 'cuffmerge_transcripts.gtf')
        self.assertFields(cuff_merge, 'species', 'Dictyostelium discoideum')
        self.assertFields(cuff_merge, 'build', 'dd-05-2009')

    @tag_process('cuffquant')
    def test_cuffquant(self):
        with self.preparation_stage():
            inputs = {
                'src': 'cuffquant_mapping.bam',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            bam = self.run_process('upload-bam', inputs)

            annotation = self.prepare_annotation(
                fn='hg19_chr20_small.gtf.gz',
                source='UCSC',
                species='Homo sapiens',
                build='hg19'
            )

        inputs = {
            'alignment': bam.id,
            'annotation': annotation.id}
        cuffquant = self.run_process('cuffquant', inputs)
        self.assertFields(cuffquant, 'species', 'Homo sapiens')
        self.assertFields(cuffquant, 'build', 'hg19')

    @tag_process('cuffnorm')
    def test_cuffnorm(self):
        with self.preparation_stage():
            inputs = {
                'src': 'cuffquant_1.cxb',
                'source': 'UCSC',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            sample_1 = self.run_process("upload-cxb", inputs)

            inputs = {
                'src': 'cuffquant_2.cxb',
                'source': 'UCSC',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            sample_2 = self.run_process("upload-cxb", inputs)

            inputs = {
                'src': 'cuffquant_3.cxb',
                'source': 'UCSC',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            sample_3 = self.run_process("upload-cxb", inputs)

            inputs = {
                'src': 'cuffquant_4.cxb',
                'source': 'UCSC',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            sample_4 = self.run_process("upload-cxb", inputs)

            inputs = {
                'src': 'cuffquant_5.cxb',
                'source': 'UCSC',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            sample_5 = self.run_process("upload-cxb", inputs)

            inputs = {
                'src': 'cuffquant_6.cxb',
                'source': 'UCSC',
                'species': 'Homo sapiens',
                'build': 'hg19'
            }
            sample_6 = self.run_process("upload-cxb", inputs)

            annotation = self.prepare_annotation(fn='hg19_chr20_small.gtf.gz', source='UCSC',
                                                 species='Homo sapiens', build='hg19')

        inputs = {
            'cuffquant': [sample_1.pk, sample_2.pk, sample_3.pk, sample_4.pk, sample_5.pk, sample_6.pk],
            'annotation': annotation.id,
            'replicates': ['1', '1', '2', '2', '2', '3']}
        cuffnorm = self.run_process('cuffnorm', inputs)
        self.assertFile(cuffnorm, 'fpkm_means', 'cuffnorm_all_fpkm_means.txt')
        self.assertFile(cuffnorm, 'genes_fpkm', 'cuffnorm_genes.fpkm_table')
        self.assertFileExists(cuffnorm, 'raw_scatter')

        exp = Data.objects.last()
        self.assertFile(exp, 'exp', 'cuffnorm_expression.tab.gz', compression='gzip')

    @tag_process('expression-bcm', 'etc-bcm')
    def test_expression_bcm(self):
        with self.preparation_stage():
            genome = self.prepare_genome()
            reads = self.prepare_reads()
            annotation = self.prepare_annotation_gff()

            inputs = {
                'genome': genome.pk,
                'reads': reads.pk,
                'annotation': annotation.pk,
                'PE_options': {
                    'library_type': "fr-unstranded"}}
            aligned_reads = self.run_process('alignment-tophat2', inputs)

            mappa = self.run_process("upload-mappability", {"src": "purpureum_mappability_50.tab.gz"})

        inputs = {
            'alignment': aligned_reads.pk,
            'gff': annotation.pk,
            'mappable': mappa.pk}
        expression = self.run_process('expression-bcm', inputs)
        self.assertFile(expression, 'rpkm', 'expression_bcm_rpkm.tab.gz', compression='gzip')
        self.assertFields(expression, "source", "DICTYBASE")
        self.assertFields(expression, 'species', 'Dictyostelium discoideum')
        self.assertFields(expression, 'build', 'dd-05-2009')
        self.assertFields(expression, 'feature_type', 'gene')

        inputs = {'expressions': [expression.pk, expression.pk]}
        etc = self.run_process('etc-bcm', inputs)
        self.assertJSON(etc, etc.output['etc'], '', 'etc.json.gz')

    @tag_process('htseq-count')
    def test_expression_htseq(self):
        with self.preparation_stage():
            genome = self.prepare_genome()
            reads = self.prepare_reads()
            inputs = {
                'src': 'annotation.gtf.gz',
                'source': 'DICTYBASE',
                'species': 'Dictyostelium discoideum',
                'build': 'dd-05-2009'
            }
            annotation = self.run_process('upload-gtf', inputs)

            inputs = {
                'genome': genome.pk,
                'reads': reads.pk,
                'annotation': annotation.pk,
                'PE_options': {'library_type': "fr-unstranded"}}
            aligned_reads = self.run_process('alignment-tophat2', inputs)

        inputs = {
            'alignments': aligned_reads.pk,
            'gff': annotation.pk,
            'stranded': "no",
            'id_attribute': 'transcript_id'}
        expression = self.run_process('htseq-count', inputs)
        self.assertFile(expression, 'rc', 'reads_rc.tab.gz', compression='gzip')
        self.assertFile(expression, 'fpkm', 'reads_fpkm.tab.gz', compression='gzip')
        self.assertFile(expression, 'exp', 'reads_tpm.tab.gz', compression='gzip')
        self.assertJSON(expression, expression.output['exp_json'], '', 'expression_htseq.json.gz')
        self.assertFields(expression, 'species', 'Dictyostelium discoideum')
        self.assertFields(expression, 'build', 'dd-05-2009')
        self.assertFields(expression, 'feature_type', 'gene')

    @tag_process('index-fasta-nucl')
    def test_index_fasta_nucl(self):
        with self.preparation_stage():
            inputs = {'src': 'HS_chr21_ensemble.fa.gz'}
            genome = self.run_process('upload-fasta-nucl', inputs)

            inputs = {
                'src': 'HS_chr21_short.gtf.gz',
                'source': 'ENSEMBL',
                'species': 'Homo sapiens',
                'build': 'ens_90'
            }
            annotation = self.run_process('upload-gtf', inputs)

        inputs = {'nucl': genome.pk, 'annotation': annotation.pk}
        index_fasta_nucl = self.run_process('index-fasta-nucl', inputs)

        del index_fasta_nucl.output['rsem_index']['total_size']  # Non-deterministic output.
        self.assertFields(index_fasta_nucl, 'rsem_index', {'dir': 'rsem'})
        self.assertFields(index_fasta_nucl, 'source', 'ENSEMBL')
        self.assertFields(index_fasta_nucl, 'species', 'Homo sapiens')
        self.assertFields(index_fasta_nucl, 'build', 'ens_90')

    @tag_process('mergeexpressions')
    def test_mergeexpression(self):
        with self.preparation_stage():
            expression_1 = self.prepare_expression(f_rc='exp_1_rc.tab.gz', f_exp='exp_1_tpm.tab.gz', f_type="TPM")
            expression_2 = self.prepare_expression(f_rc='exp_2_rc.tab.gz', f_exp='exp_2_tpm.tab.gz', f_type="TPM")
            expression_3 = self.prepare_expression(f_rc='exp_2_rc.tab.gz', f_exp='exp_2_tpm.tab.gz', f_type="RC")

        inputs = {
            'exps': [expression_1.pk, expression_2.pk],
            'genes': ['DPU_G0067096', 'DPU_G0067098', 'DPU_G0067102']
        }

        mergeexpression_1 = self.run_process('mergeexpressions', inputs)
        self.assertFile(mergeexpression_1, "expset", "merged_expset_subset.tab")

        inputs = {
            'exps': [expression_1.pk, expression_2.pk],
            'genes': []
        }

        mergeexpression_2 = self.run_process('mergeexpressions', inputs)
        self.assertFile(mergeexpression_2, "expset", "merged_expset_all.tab")

        inputs = {
            'exps': [expression_1.pk, expression_2.pk, expression_3.pk],
            'genes': ['DPU_G0067096', 'DPU_G0067098', 'DPU_G0067102']
        }
        self.run_process('mergeexpressions', inputs, Data.STATUS_ERROR)

    @tag_process('mergeetc')
    def test_etcmerge(self):
        with self.preparation_stage():
            genome = self.prepare_genome()
            reads = self.prepare_reads()
            annotation = self.prepare_annotation_gff()

            inputs = {
                'genome': genome.pk,
                'reads': reads.pk,
                'annotation': annotation.pk,
                'PE_options': {
                    'library_type': "fr-unstranded"}}
            aligned_reads = self.run_process('alignment-tophat2', inputs)

            mappa = self.run_process("upload-mappability", {"src": "purpureum_mappability_50.tab.gz"})

            inputs = {
                'alignment': aligned_reads.pk,
                'gff': annotation.pk,
                'mappable': mappa.pk}

            expression = self.run_process('expression-bcm', inputs)

            inputs = {'expressions': [expression.pk, expression.pk]}
            etc = self.run_process('etc-bcm', inputs)

        inputs = {
            'exps': [etc.pk],
            'genes': ['DPU_G0067110', 'DPU_G0067098', 'DPU_G0067102']
        }

        etcmerge = self.run_process('mergeetc', inputs)
        self.assertFile(etcmerge, "expset", "merged_etc.tab.gz", compression='gzip')

    @tag_process('feature_counts')
    def test_feature_counts(self):
        with self.preparation_stage():
            inputs = {
                'src': 'annotation.gtf.gz',
                'source': 'DICTYBASE',
                'species': 'Dictyostelium discoideum',
                'build': 'dd-05-2009'
            }
            annotation_gtf = self.run_process('upload-gtf', inputs)
            annotation_gff3 = self.prepare_annotation_gff()

            bam_single_inputs = {
                'src': 'reads.bam',
                'species': 'Dictyostelium discoideum',
                'build': 'dd-05-2009'
            }
            bam_single = self.run_process('upload-bam', bam_single_inputs)

            inputs = {
                'src': 'feature_counts_paired.bam',
                'species': 'Dictyostelium discoideum',
                'build': 'dd-05-2009'
            }
            bam_paired = self.run_process('upload-bam', inputs)

        inputs = {
            'alignments': bam_paired.id,
            'annotation': annotation_gtf.id,
            'id_attribute': 'transcript_id',
            'PE_options': {
                'is_paired_end': True,
                'require_both_ends_mapped': True
            }
        }

        expression = self.run_process('feature_counts', inputs)
        self.assertFile(expression, 'rc', 'feature_counts_out_rc.tab.gz', compression='gzip')
        self.assertFile(expression, 'fpkm', 'feature_counts_out_fpkm.tab.gz', compression='gzip')
        self.assertFile(expression, 'exp', 'feature_counts_out_tpm.tab.gz', compression='gzip')
        self.assertFields(expression, 'species', 'Dictyostelium discoideum')
        self.assertFields(expression, 'build', 'dd-05-2009')
        self.assertFields(expression, 'feature_type', 'gene')

        inputs = {
            'alignments': bam_single.id,
            'annotation': annotation_gff3.id,
            'id_attribute': 'Parent'}
        expression = self.run_process('feature_counts', inputs)
        self.assertFile(expression, 'rc', 'reads_rc.tab.gz', compression='gzip')
        self.assertFile(expression, 'fpkm', 'reads_fpkm.tab.gz', compression='gzip')
        self.assertFile(expression, 'exp', 'reads_tpm.tab.gz', compression='gzip')
        self.assertFields(expression, 'feature_type', 'gene')

    @tag_process('salmon-index')
    def test_salmon_index(self):
        with self.preparation_stage():
            cds = self.run_process('upload-fasta-nucl', {'src': 'salmon_cds.fa.gz'})

        inputs = {
            'nucl': cds.id,
            'source': 'ENSEMBL',
            'species': 'Homo sapiens',
            'build': 'ens_90',
        }
        salmon_index = self.run_process('salmon-index', inputs)

        del salmon_index.output['index']['total_size']  # Non-deterministic output.
        self.assertFields(salmon_index, 'index', {'dir': 'salmon_index'})
        self.assertFields(salmon_index, 'source', 'ENSEMBL')
        self.assertFields(salmon_index, 'species', 'Homo sapiens')
        self.assertFields(salmon_index, 'build', 'ens_90')
