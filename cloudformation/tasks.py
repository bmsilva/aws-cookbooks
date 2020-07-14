import json

from invoke import task, Collection


DEFAULT_REGION = 'eu-west-1'


@task
def check_stack_status(ctx, name, region=DEFAULT_REGION):
    cmd = [
        'aws',
        'cloudformation',
        'describe-stacks',
        '--stack-name', name,
        '--region', region,
    ]

    result = ctx.run(' '.join(cmd), hide='out')
    out = result.stdout
    response = json.loads(out)

    stack = response['Stacks'][0]
    print('StackName: ', stack['StackName'])
    print('Description: ', stack['Description'])
    print('Stack Status: ', stack['StackStatus'])
    if 'Outputs' in stack:
        print('Outputs: ', json.dumps(stack['Outputs'], indent=4))


@task
def delete_stack(ctx, stack_name, region=DEFAULT_REGION):
    cmd = [
        'aws',
        'cloudformation',
        'delete-stack',
        '--stack-name', stack_name,
        '--region', region,
    ]

    ctx.run(' '.join(cmd))


@task
def create_vpc(ctx, name, region=DEFAULT_REGION):
    r"""Deploy a CloudFormation template that creates a new VPC
    ex:
        invoke create-vpc --name stack-name \
                          --region eu-west-1
    """
    cmd = [
        'aws',
        'cloudformation',
        'create-stack',
        '--stack-name', name,
        '--region', region,
        '--template-body', 'file://cftemplates/vpc_3az.yml',
    ]
    ctx.run(' '.join(cmd))


@task
def update_vpc(ctx, name, region=DEFAULT_REGION):
    r"""Deploy an update of CloudFormation template that creates a VPC
    ex:
        invoke update-vpc --name stack-name \
                          --region eu-west-1
    """
    cmd = [
        'aws',
        'cloudformation',
        'update-stack',
        '--stack-name', name,
        '--region', region,
        '--template-body', 'file://cftemplates/vpc_3az.yml',
    ]
    ctx.run(' '.join(cmd))


@task
def destroy_vpc(ctx, name, region=DEFAULT_REGION):
    delete_stack(ctx, name, region)


@task
def check_vpc_status(ctx, name, region=DEFAULT_REGION):
    check_stack_status(ctx, name, region)


@task
def list_secrets(ctx):
    cmd = [
        'aws',
        'secretsmanager',
        'list-secrets',
    ]

    ctx.run(' '.join(cmd))


@task
def create_db_credentials(ctx, name, username, password):
    secret = {
        'username': username,
        'password': password,
    }
    secret_string = json.dumps(secret)
    cmd = [
        'aws',
        'secretsmanager',
        'create-secret',
        '--name', name,
        '--secret-string', f"'{secret_string}'",
    ]

    ctx.run(' '.join(cmd))


@task
def destroy_db_credentials(ctx, name):
    cmd = [
        'aws',
        'secretsmanager',
        'delete-secret',
        '--secret-id', name,
    ]

    ctx.run(' '.join(cmd))


@task
def get_db_credentials(ctx, name):
    cmd = [
        'aws',
        'secretsmanager',
        'get-secret-value',
        '--secret-id', name,
    ]

    result = ctx.run(' '.join(cmd), hide='out')
    out = result.stdout
    response = json.loads(out)

    secret = json.loads(response['SecretString'])
    print('Username: ', secret['username'])
    print('Password:: ', secret['password'])


@task
def create_db(ctx, stack_name, vpc_stack_name, secretsmanager_name,
              region=DEFAULT_REGION):
    r"""Deploy a CF Template that creates a Postgres Aurora Serverless DB
    ex:
        invoke create-db --stack-name stack-name \
                         --region eu-west-1 \
                         --vpc-stack-name app-vpc-dev \
                         --secretsmanager-name pg-serverless-db
    """
    parameters = [
        ('AppVpcStackName', vpc_stack_name),
        ('DbCredentialsSecretName', secretsmanager_name),
    ]
    parameters_string = ' '.join(
        (f'ParameterKey={k},ParameterValue={v}' for k, v in parameters))
    cmd = [
        'aws',
        'cloudformation',
        'create-stack',
        '--stack-name', stack_name,
        '--region', region,
        '--template-body', 'file://cftemplates/pg_serverless.yml',
        '--parameters', parameters_string
    ]
    ctx.run(' '.join(cmd))


@task
def update_db(ctx, stack_name, vpc_stack_name, secretsmanager_name,
              region=DEFAULT_REGION):
    r"""Deploy a CF Template that creates a Postgres Aurora Serverless DB
    ex:
        invoke update-db --stack-name stack-name \
                         --region eu-west-1 \
                         --vpc-stack-name app-vpc-dev \
                         --secretsmanager-name pg-serverless-db
    """
    parameters = [
        ('AppVpcStackName', vpc_stack_name),
        ('DbCredentialsSecretName', secretsmanager_name),
    ]
    parameters_string = ' '.join(
        (f'ParameterKey={k},ParameterValue={v}' for k, v in parameters))
    cmd = [
        'aws',
        'cloudformation',
        'update-stack',
        '--stack-name', stack_name,
        '--region', region,
        '--template-body', 'file://cftemplates/pg_serverless.yml',
        '--parameters', parameters_string
    ]
    ctx.run(' '.join(cmd))


@task
def check_db_status(ctx, name, region=DEFAULT_REGION):
    check_stack_status(ctx, name, region)


@task
def destroy_db(ctx, stack_name, region=DEFAULT_REGION):
    inp = input("Have you removed the delete protection (yes/no)? ")
    if inp == 'yes':
        delete_stack(ctx, stack_name, region)


@task
def create_keypair(ctx, name):
    r"""Create a keypair that can be used for EC2 instances
    ex:
        invoke create-keypair --name mykeypair
    """
    cmd = [
        "aws",
        "ec2",
        "create-key-pair",
        "--key-name", name,
    ]

    result = ctx.run(' '.join(cmd), hide='out')
    out = result.stdout
    keypair = json.loads(out)

    with open(f'{name}.pem', 'w') as fh:
        fh.write(keypair['KeyMaterial'])

    print(keypair['KeyName'], '=', keypair['KeyPairId'])
    print(keypair['KeyFingerprint'])


@task
def destroy_keypair(ctx, name):
    r"""Destroy a keypair
    ex:
        invoke destroy-keypair --name mykeypair
    """
    cmd = [
        "aws",
        "ec2",
        "delete-key-pair",
        "--key-name", name,
    ]

    ctx.run(' '.join(cmd))


@task
def create_ec2(ctx, stack_name, vpc_stack_name, ssh_cidr="0.0.0.0/0",
               keypair_name='ec2keypair', region=DEFAULT_REGION):
    r"""Deploy a CF Template that creates an EC2 instance
    ex:
        invoke create-db --stack-name stack-name \
                         --region eu-west-1 \
                         --vpc-stack-name app-vpc-dev \
    """
    parameters = [
        ('AppVpcStackName', vpc_stack_name),
        ('SshCidrBlock', ssh_cidr),
        ('Ec2KeyName', keypair_name),
    ]
    parameters_string = ' '.join(
        (f'ParameterKey={k},ParameterValue={v}' for k, v in parameters))
    cmd = [
        'aws',
        'cloudformation',
        'create-stack',
        '--stack-name', stack_name,
        '--region', region,
        '--template-body', 'file://cftemplates/ec2_on_pub_subnet.yml',
        '--parameters', parameters_string,
    ]
    ctx.run(' '.join(cmd))


@task
def update_ec2(ctx, stack_name, vpc_stack_name, ssh_cidr='0.0.0.0/0',
               keypair_name='ec2keypair', region=DEFAULT_REGION):
    r"""Deploy an update of CloudFormation template that creates an EC2
    ex:
        invoke update-ec2 --stack-name stack-name \
                          --region eu-west-1 \
                          --vpc-stack-name app-vpc-dev
    """
    parameters = [
        ('AppVpcStackName', vpc_stack_name),
        ('SshCidrBlock', ssh_cidr),
        ('Ec2KeyName', keypair_name),

    ]
    parameters_string = ' '.join(
        (f'ParameterKey={k},ParameterValue={v}' for k, v in parameters))
    cmd = [
        'aws',
        'cloudformation',
        'update-stack',
        '--stack-name', stack_name,
        '--region', region,
        '--template-body', 'file://cftemplates/ec2_on_pub_subnet.yml',
        '--parameters', parameters_string,
    ]
    ctx.run(' '.join(cmd))


@task
def destroy_ec2(ctx, stack_name, region=DEFAULT_REGION):
    delete_stack(ctx, stack_name, region)


@task
def check_ec2_status(ctx, name, region=DEFAULT_REGION):
    check_stack_status(ctx, name, region)


ns = Collection()
ns.configure({})
ns.add_task(check_stack_status)
ns.add_task(delete_stack)
ns.add_task(create_vpc)
ns.add_task(update_vpc)
ns.add_task(destroy_vpc)
ns.add_task(check_vpc_status)
ns.add_task(list_secrets)
ns.add_task(create_db_credentials)
ns.add_task(destroy_db_credentials)
ns.add_task(get_db_credentials)
ns.add_task(create_db)
ns.add_task(update_db)
ns.add_task(destroy_db)
ns.add_task(check_db_status)
ns.add_task(create_keypair)
ns.add_task(destroy_keypair)
ns.add_task(create_ec2)
ns.add_task(update_ec2)
ns.add_task(destroy_ec2)
ns.add_task(check_ec2_status)
