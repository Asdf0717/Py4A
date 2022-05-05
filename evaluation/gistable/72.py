import tensorflow as tf
import numpy as np
import uuid

x = tf.placeholder(shape=[None, 3], dtype=tf.float32)
nn = tf.layers.dense(x, 3, activation=tf.nn.sigmoid)
nn = tf.layers.dense(nn, 5, activation=tf.nn.sigmoid)
encoded = tf.layers.dense(nn, 2, activation=tf.nn.sigmoid)
nn = tf.layers.dense(encoded, 5, activation=tf.nn.sigmoid)
nn = tf.layers.dense(nn, 3, activation=tf.nn.sigmoid)

cost = tf.reduce_mean((nn - x)**2)
optimizer = tf.train.RMSPropOptimizer(0.01).minimize(cost)
init = tf.global_variables_initializer()

tf.summary.scalar("cost", cost)
merged_summary_op = tf.summary.merge_all()

with tf.Session() as sess:
    sess.run(init)
    uniq_id = "/tmp/tensorboard-layers-api/" + uuid.uuid1().__str__()[:6]
    summary_writer = tf.summary.FileWriter(uniq_id, graph=tf.get_default_graph())
    x_vals = np.random.normal(0, 1, (10000, 3))
    for step in range(10000):
        _, val, summary = sess.run([optimizer, cost, merged_summary_op],
                                   feed_dict={x: x_vals})
        if step % 5 == 0:
            print("step: {}, value: {}".format(step, val))
            summary_writer.add_summary(summary, step)