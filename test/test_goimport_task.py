import os
import shutil

from pipeline.tasks import protoc_tasks


def test_golang_update_imports_task(tmpdir):
    task = protoc_tasks.GoLangUpdateImportsTask('test')
    output_dir = tmpdir.mkdir('out')
    final_repo_dir = tmpdir.mkdir('final')
    pkg_dir = output_dir.mkdir('fake-gen-go')
    shutil.copy('test/fake-repos/fake-proto/fake.pb.go', str(pkg_dir))
    task.execute(api_name='fake', language='go',
                 go_import_base='example.com/fake',
                 output_dir=str(output_dir),
                 final_repo_dir=str(final_repo_dir))
    with open(os.path.join(str(final_repo_dir), 'proto', 'fake.pb.go')) as f:
        actual = f.read()
    with open('test/testdata/go_grpc_expected_fake.pb.go') as f:
        expected = f.read()
    assert actual == expected
