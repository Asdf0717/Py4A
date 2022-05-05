from keras.optimizers import Adam
from keras import backend as K
from keras.datasets import mnist
from keras.utils.np_utils import to_categorical
from keras.metrics import categorical_accuracy
from keras.initializations import glorot_uniform, zero
import numpy as np

# inputs and targets are placeholders
input_dim = 28*28
output_dim = 10
x = K.placeholder(name="x", shape=(None, input_dim))
ytrue = K.placeholder(name="y", shape=(None, output_dim))

# model parameters are variables
hidden_dim = 128
W1 = glorot_uniform((input_dim,hidden_dim))
b1 = zero((hidden_dim,))
W2 = glorot_uniform((hidden_dim,output_dim))
b2 = zero((output_dim,))
params = [W1, b1, W2, b2]

# two-layer model
hidden = K.sigmoid(K.dot(x, W1)+b1)
ypred = K.softmax(K.dot(hidden,W2)+b2)

# categorical cross entropy loss
loss = K.mean(K.categorical_crossentropy(ytrue, ypred),axis=None)

# categorical accuracy
accuracy = categorical_accuracy(ytrue, ypred)

# Train function
opt = Adam()
updates = opt.get_updates(params, [], loss)
train = K.function([x, ytrue],[loss, accuracy],updates=updates)

# Test function
test = K.function([x, ytrue], [loss, accuracy])

# Train the network
((xtrain, ytrain),(xtest, ytest)) = mnist.load_data()
(xtrain, xtest) = [x.reshape((-1, input_dim))/255.0 for x in (xtrain, xtest)]
(ytrain, ytest) = [to_categorical(y, output_dim) for y in (ytrain, ytest)]
for epoch in range(1000):
	loss, accuracy = train([xtrain, ytrain])
	test_loss, test_accuracy = test([xtest, ytest])
	print("Epoch: {}, Train Loss: {}, Train Accuracy: {}, Test Loss: {}, Test Accuracy: {}".format(
		epoch, loss, accuracy, test_loss, test_accuracy))

