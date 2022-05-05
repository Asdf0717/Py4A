import numpy as NP
import casadi as C
def qpsolve(H,g,lbx,ubx,A=NP.zeros((0,0)),lba=NP.zeros(0),uba=NP.zeros(0)):
    # Convert to CasADi types
    H = C.DMatrix(H)
    g = C.DMatrix(g)
    lbx = C.DMatrix(lbx)
    ubx = C.DMatrix(ubx)
    A = C.DMatrix(A)
    A = A.reshape((A.size1(),H.size1())) # Make sure matching dimensions
    lba = C.DMatrix(lba)
    uba = C.DMatrix(uba)

    # QP structure
    qp = C.qpStruct(h=H.sparsity(),a=A.sparsity())

    # Create CasADi solver instance
    if False:
        solver = C.QpSolver("qpoases",qp)
    else:
        solver = C.QpSolver("nlp",qp)
        solver.setOption("nlp_solver","ipopt")    

    # Set options
    #solver.setOption("option_name", ...)
    
    # Initialize the solver
    solver.init()
    
    # Pass problem data
    solver.setInput(H,"h")
    solver.setInput(g,"g")
    solver.setInput(A,"a")
    solver.setInput(lbx,"lbx")
    solver.setInput(ubx,"ubx")
    solver.setInput(lba,"lba")
    solver.setInput(uba,"uba")

    # Solver the QP
    solver.evaluate()
    
    # Return the solution
    return NP.array(solver.getOutput("x"))