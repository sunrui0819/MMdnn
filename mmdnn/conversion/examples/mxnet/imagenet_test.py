#----------------------------------------------------------------------------------------------
#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License. See License.txt in the project root for license information.
#----------------------------------------------------------------------------------------------

from collections import namedtuple
import numpy as np
from mmdnn.conversion.examples.imagenet_test import TestKit
import mxnet as mx

Batch = namedtuple('Batch', ['data'])


class TestMXNet(TestKit):

    def __init__(self):
        super(TestMXNet, self).__init__()

        self.truth['tensorflow']['inception_v3'] = [(22, 9.6691055), (24, 4.3524752), (25, 3.5957956), (132, 3.5657482), (23, 3.3462858)]
        self.truth['keras']['inception_v3'] = [(21, 0.93430501), (23, 0.0028834261), (131, 0.0014781745), (24, 0.0014518937), (22, 0.0014435325)]

        self.model = self.MainModel.RefactorModel()
        self.model = self.MainModel.deploy_weight(self.model, self.args.w)


    def preprocess(self, image_path):
        self.data = super(TestMXNet, self).preprocess(image_path)
        self.data = np.swapaxes(self.data, 0, 2)
        self.data = np.swapaxes(self.data, 1, 2)
        self.data = np.expand_dims(self.data, 0)


    def print_result(self):
        self.model.forward(Batch([mx.nd.array(self.data)]))
        prob = self.model.get_outputs()[0].asnumpy()
        super(TestMXNet, self).print_result(prob)


    def inference(self, image_path):
        self.preprocess(image_path)

        # self.print_intermediate_result('InceptionV3/InceptionV3/Mixed_5b/Branch_3/AvgPool_0a_3x3/AvgPool', False)

        self.print_result()

        self.test_truth()


    def print_intermediate_result(self, layer_name, if_transpose = False):
        internals = self.model.symbol.get_internals()
        intermediate_output = internals[layer_name + "_output"]
        test_model = mx.mod.Module(symbol = intermediate_output, context = mx.cpu(), data_names = ['input'])
        if self.args.preprocess == 'vgg19' or self.args.preprocess == 'inception_v1':
            test_model.bind(for_training = False, data_shapes = [('input', (1, 3, 224, 224))])
        elif self.args.preprocess == 'resnet' or self.args.preprocess == 'inception_v3':
            test_model.bind(for_training = False, data_shapes = [('input', (1, 3, 299, 299))])
        else:
            assert False

        arg_params, aux_params = self.model.get_params()

        test_model.set_params(arg_params = arg_params, aux_params = aux_params, allow_missing = True, allow_extra = True)
        test_model.forward(Batch([mx.nd.array(self.data)]))
        intermediate_output = test_model.get_outputs()[0].asnumpy()

        super(TestMXNet, self).print_intermediate_result(intermediate_output, if_transpose)


    def dump(self, path = None):
        if path is None: path = self.args.dump
        self.model.save_checkpoint(path, 0)
        print ('MXNet checkpoint file is saved with prefix [{}] and iteration 0, generated by [{}.py] and [{}].'.format(
            path, self.args.n, self.args.w))


if __name__ == '__main__':
    tester = TestMXNet()
    if tester.args.dump:
        tester.dump()
    else:
        tester.inference(tester.args.image)
