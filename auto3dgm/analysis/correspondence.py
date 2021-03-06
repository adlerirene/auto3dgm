from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy import linalg
from scipy.optimize import linear_sum_assignment
from scipy.spatial import distance_matrix
import numpy as np

class Correspondence:
    #params: self,
    #meshes: either a mesh object or a list or a dictionary of mesh objects
    #meshes: a list of meshes 
    #globalize: flag for performing globalized pairwise alignment (default:yes)
    #mirror: flag for allowing mirrored meshes (default: no)
    #reference_index= index of the mesh that other meshes are aligned against
    def __init__(self, meshes, globalize=1, mirror=0, reference_index=0):
        self.globalize=globalize
        self.mirror=mirror
        if isinstance(meshes,(list,dict)):
            if isinstance(meshes,(list,)):
                self.mesh_list=meshes
            if isinstance(meshes,(dict,)):
                self.mesh_list=meshes.keys()
            if(reference_index>len(meshes)-1):
                msg = 'There are fewer meshes than the given reference_index'
                raise OSError(msg)
            else:
                 self.reference_index=reference_index
    @staticmethod
    def find_mst(distance_matrix):
        X = csr_matrix([t for t in distance_matrix])
        output = minimum_spanning_tree(X)
        return output.toarray()
    #An auxiliary method for computing the initial pairwise-alignment
    #Computes the principal components of two meshes and all possible rotations of the 3-axes)
    #params: mesh1, mesh2 meshes that have vertices that are 3 x n matrices
    #        mirror: a flag for whether or not mirror images of the shapes should be considered
    def principal_component_alignment(mesh1,mesh2,mirror):
        X=mesh1.vertices
        Y=mesh2.vertices
        UX,DX,VX =linalg.svd(X, full_matrices=False)
        UY,DY,VY =linalg.svd(Y, full_matrices=False)
        P=[]
        R=[]
	P.append(np.array([1,1,1]))
	P.append(np.array([1,-1,-1]))
	P.append(np.array([-1,-1,1]))
	P.append(np.array([-1,1,-1]))
        if(mirror==1):
            P.append(np.array([-1,1,1]))
            P.append(np.array([1,-1,1]))
            P.append(np.array([1,1,-1]))
            P.append(np.array([-1,-1,-1]))
        for i in P:
            R.append(np.dot(UX*i,UY.T))
        return R
    
    @staticmethod
    #Computes the best possible initial alignment for meshes 1 and 2
    #Mesh 1 is used as the reference
    #params: mesh1, mesh2 meshes that have vertices that are 3 x n matrices
    #        mirror: a flag for whether or not mirror images of the shapes should be considered
    def best_pairwise_PCA_alignment(mesh1,mesh2,self):
        R=self.principal_component_alignment(mesh1,mesh2,self.mirror)
        permutations = []
        for rot, i in zip(R, range(len(R))):
            min_cost = np.ones(len(R))*np.inf
            cost = distance_matrix(mesh1.T, np.dot(rot, mesh2).T)
            #The hungarian algorithm:
            V1_ind, V2_ind = linear_sum_assignment(cost)
            min_cost[i] = np.sqrt(np.sum(cost[V1_ind, V2_ind]))
            permutations.append(V2_ind)
        best_rot_ind = np.argmin(min_cost)
        best_permutation = permutations[best_rot_ind]
        best_rot = R[best_rot_ind]
        #Needed?
        new_mesh2 = np.dot(best_rot.T, mesh2)
        return(new_mesh2)

    @staticmethod
    #Returns the meshed aligned by the initial PCA component pairing.
    #Everything is aligned against the mesh specified by the reference_index
    def initial_rotation(self):
        mesh1=self.mesh_list[self.reference_index]
        Rotations=[]
        for i in self.mesh_list:
            Rotations.append(self.best_pairwise_PCA_alignment(mesh1,i,self))
        return(Rotations)
        