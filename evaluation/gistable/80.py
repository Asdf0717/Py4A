"""Visualize stability of stochastic gradient descent for finding a linear
separator."""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

np.random.seed(1)
mpl.rcParams['axes.linewidth'] = 0.0

# create point clouds
num_points = 30
bluepts = np.random.normal(0,1,(num_points, 2))
redpts = np.random.normal(0,1,(num_points,2))
bluepts[:,0] -= 1.1*np.ones((num_points,))
bluepts[0,:] = -np.ones(2)
redpts[:,0] += 1.1*np.ones((num_points,))
bluepts2 = np.copy(bluepts)
bluepts2[0,:] = np.ones(2)

# compute one pass of SGD over the data
sgdpts = np.ones((num_points+1,2))
sgdpts[0,:] = np.array([0,1.0])
sgdpts2 = np.copy(sgdpts)
step_size = 1.0/num_points
for i in xrange(num_points):
  grad = np.multiply(sgdpts[i, :], bluepts[i,:]**2) + bluepts[i,:]
  grad2 = np.multiply(sgdpts2[i, :], bluepts2[i,:]**2) + bluepts2[i,:]
  sgdpts[i+1,:] = sgdpts[i, :] - step_size * grad
  sgdpts2[i+1,:] = sgdpts2[i, :] - step_size * grad2
  grad = np.multiply(sgdpts[i+1, :], redpts[i,:]**2) - redpts[i,:]
  sgdpts[i+1,:] = sgdpts[i+1, :] - step_size * grad
  sgdpts2[i+1,:] = sgdpts2[i+1, :] - step_size * grad

def hyperplane(w):
  w /= np.linalg.norm(w)
  x = np.linspace(-200,100,100)
  y = -1.0 * w[0] * x / w[1]
  return x, y

for i in xrange(num_points):
  fig = plt.figure(figsize=(6,6), facecolor='white', frameon=False, dpi=300)
  plt.plot(bluepts[1:,0],bluepts[1:,1],'bo', ms=8)
  plt.plot(redpts[:,0],redpts[:,1],'r^', ms=8)
  ax = plt.axes()
  ax.arrow(-0.95, -0.95, 1.82, 1.82, head_width=0.05, fc='#cccccc', ec='#cccccc', lw=2)
  plt.plot(bluepts[0,0],bluepts[0,0], marker='o', color='green', ms=8)
  plt.plot(bluepts2[0,0],bluepts2[0,0], marker='o', color='purple', ms=8)
  plt.xlim(-2,2)
  plt.ylim(-2,2)
  x, y = hyperplane(sgdpts[i,:])
  plt.plot(x, y, 'g-')
  x2, y2 = hyperplane(sgdpts2[i,:])
  plt.plot(x2, y2, color='purple')
  ax.fill_between(x, y, y+100, color=(0.9, 0.9, 0.9))
  ax.fill_between(x, y, y2, color=(0.1, 0.5, 0.5))
  ax.axes.get_xaxis().set_visible(False)
  ax.axes.get_yaxis().set_visible(False)
  plt.savefig(str(i).zfill(2)+'.png', bbox_inches='tight', pad_inches=0)
  plt.close()
