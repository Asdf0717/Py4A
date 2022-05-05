"""
wGAN implemented on top of tensorflow as described in: [Wasserstein GAN](https://arxiv.org/pdf/1701.07875.pdf)
with improvements as described in: [Improved Training of Wasserstein GANs](https://arxiv.org/pdf/1704.00028.pdf).

"""

import tensorflow as tf


#
# define earth mover distance (wasserstein loss)
#

def em_loss(y_coefficients, y_pred):
    return tf.reduce_mean(tf.multiply(y_coefficients, y_pred))

#
# construct computation graph for calculating the gradient penalty (improved wGAN) and training the discriminator
#

# sample a batch of noise (generator input)
_z = tf.placeholder(tf.float32, shape=(batch_size, rand_dim))

# sample a batch of real images
_x = tf.placeholder(tf.float32, shape=(batch_size, img_height, img_width, img_channels))

# generate a batch of images with the current generator
_g_z = generator_model(_z)

# calculate `x_hat`
epsilon = tf.placeholder(tf.float32, shape=(batch_size, 1, 1, 1))
x_hat = epsilon * _x + (1.0 - epsilon) * _g_z

# gradient penalty
gradients = tf.gradients(discriminator_model(x_hat), [x_hat])
_gradient_penalty = 10.0 * tf.square(tf.norm(gradients[0], ord=2) - 1.0)

# calculate discriminator's loss
_disc_loss = em_loss(tf.ones(batch_size), discriminator_model(_g_z)) - \
    em_loss(tf.ones(batch_size), discriminator_model(_x)) + \
    _gradient_penalty