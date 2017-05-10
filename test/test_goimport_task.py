# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil

from artman.tasks import protoc_tasks


def test_golang_update_imports_task(tmpdir):
    task = protoc_tasks.GoLangUpdateImportsTask('test')
    output_dir = tmpdir.mkdir('out')
    gapic_code_dir = tmpdir.mkdir('final')
    go_dir = output_dir.mkdir('go')
    pkg_dir = go_dir.mkdir('grpc-google-cloud-fake-v1')
    shutil.copy('test/fake-repos/fake-proto/fake.pb.go', str(pkg_dir))
    task.execute(api_name='fake', api_version='v1', language='go',
                 organization_name='google-cloud',
                 go_import_base='example.com/fake',
                 output_dir=str(output_dir),
                 gapic_code_dir=str(gapic_code_dir))
    with open(os.path.join(str(gapic_code_dir), 'proto', 'fake.pb.go')) as f:
        actual = f.read()
    with open('test/testdata/go_grpc_expected_fake.pb.go') as f:
        expected = f.read()
    assert actual == expected
