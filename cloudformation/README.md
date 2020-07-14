# Tipical scenarios

## Setup a Postgresql Aurora serverless database from scratch

If we want to create it in a new VPC, we can use this baseline:

```
invoke create-vpc --name <vpc-name> --region <vpc-region>
```

Then we should store the database credentials on Secrets Manager Service.

```
invoke create-db-credentials \
    --name <secret-name> \
    --username <dbusername> \
    --password <dbpassword>
```

We are ready now to launch the database cloudformation

```
invoke create-db --stack-name <stack-name> \
    --vpc-stack-name <vpc-name-used-above> \
    --secretsmanager-name <secret-name-used-above>
```

To test it, we can launch an EC2 on the public subnet and then ssh to it.
We can use an existent keypair, but if we need a new one we can just create it:

```
invoke create-keypair --name <ec2-keypair-name>
```

Now let's launch the EC2 cloudformation template, optionally we can indicate an
ssh cidr block to not make the ssh port available to all the internet

```
invoke create-ec2 \
    --stack-name <ec2-stack-name> \
    --vpc-stack-name <vpc-name-used-above-> \
    --ssh-cidr <XXX.XXX.XXX.XXX/XX>
```
