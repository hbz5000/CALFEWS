from calfews_src.model_cy cimport Model

cdef class main_cy():
 
  cdef:

    public double progress
    public int running_sim
    public Model modelno, modelso

  cdef void run(self, str results_folder, str model_mode, str flow_input_type, str flow_input_source)