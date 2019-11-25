provider "azurerm" {
  subscription_id = "dce6a845-0413-49b4-8713-79b1ea22f752"
  client_id = "9ca70ed3-b3b3-4d3d-8b81-6c6c318f01d2"
  client_secret = "de96f31d-b37d-4ee2-87da-0a79ac165306"
  tenant_id = "67408e06-b199-4d27-aee7-677296c170ce"
}

resource "random_id" "vmID" {
  byte_length = 4
}

# GENERAL RESOURCES

resource "azurerm_resource_group" "vmResourceGroup" {
    name     = "ButtonDynamicResourceGroup"
    location = "northeurope"
}

resource "azurerm_virtual_network" "vmVN" {
  name                = "vmNetwork"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.vmResourceGroup.location
  resource_group_name = azurerm_resource_group.vmResourceGroup.name
}

resource "azurerm_subnet" "internal" {
  name                 = "internal"
  resource_group_name  = azurerm_resource_group.vmResourceGroup.name
  virtual_network_name = azurerm_virtual_network.vmVN.name
  address_prefix       = "10.0.2.0/24"
}

resource "azurerm_network_security_group" "vmNetSecurityGroup" {
    name                = "vmNetSecurityGroup"
    location            = "northeurope"
    resource_group_name = azurerm_resource_group.vmResourceGroup.name
    
    security_rule {
        name                       = "SSH"
        priority                   = 1001
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "22"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    security_rule {
        name                       = "HTTP"
        priority                   = 1002
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "80"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }
}

# END OF GENERAL RESOURCES


# VM SPECIFIC RESOURCES

# Create public IPs
resource "azurerm_public_ip" "vmPublicIP" {
    name                = "vmIP-${random_id.vmID.hex}"
    location            = "northeurope"
    resource_group_name = azurerm_resource_group.vmResourceGroup.name
    allocation_method   = "Dynamic"
}

# Create network interface
resource "azurerm_network_interface" "vmNIC" {
  name                = "vmNIC-${random_id.vmID.hex}"
  location            = azurerm_resource_group.vmResourceGroup.location
  resource_group_name = azurerm_resource_group.vmResourceGroup.name

  ip_configuration {
    name                          = "testconfiguration1"
    subnet_id                     = azurerm_subnet.internal.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vmPublicIP.id
  }
}

# Create virtual machine
resource "azurerm_virtual_machine" "vm" {
    name                          = "vm-${random_id.vmID.hex}"
    location                      = "northeurope"
    resource_group_name           = azurerm_resource_group.vmResourceGroup.name
    network_interface_ids         = [azurerm_network_interface.vmNIC.id]
    vm_size                       = "Standard_B1ls"
    delete_os_disk_on_termination = true

    storage_os_disk {
        name              = "vmDisk-${random_id.vmID.hex}"
        caching           = "ReadWrite"
        create_option     = "FromImage"
        managed_disk_type = "StandardSSD_LRS"
    }

    storage_image_reference {
        publisher = "Canonical"
        offer     = "UbuntuServer"
        sku       = "18.04-LTS"
        version   = "latest"
    }

    os_profile {
        computer_name  = "vm-${random_id.vmID.hex}"
        admin_username = "vmadmin"
    }

    os_profile_linux_config {
        disable_password_authentication = true
        ssh_keys {
            path     = "/home/vmadmin/.ssh/authorized_keys"
            key_data = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC+aeGXi7/oWkbjdIBnr5Htd8X9tCY+OyCpi4y1V4779cyLinTDtIM/O/fcccnSYBSCi/YsdzlK198uSsCx2uMVvxYTvguOmdmxoBKeeMNEViW4InUr41SsRLYiTK71afAIMlvxMFCoynWEMMUrQH/zZNCgw80RefB3DFSn1N+usi18nwxzqyQ+8KEIpCGSexfvd8zo4+X0817ZUo+ssUDSBcAnM8/FjsBImEAB7+llD/cyJPkV9xslU5iwUohjm6ISVY/Kwc9sfI5pw37XCHDPprMQfh+HyVIiX1eBvh8ZYVdybsl6UNke+wMvZSSKI/3bmm/Jb8IuspYy30GoEyR8Tj0g95LHsl/+MUB3Js/Poi23VD28uszlWpsNmGOLxdLlZgQvb8vzfdoS4aHGDAmY14oRQTC+dHBTIcg22f/2wVxK1uoTOAN+e9gOYUH8re9RuZfL89rpdBg4DyPup8+PCIUmtFdq+qMtFw2l07GWs2G6rstzJJXxBFbG9G8b7NsZE1poPdCT+cFW9FK0bcjGTPto5hvLcL5ggb+bH9H1QRYWgLuiBTy7qEmE+7PdoUX4h1VlRdJW/Oroq9cSM4w9OtogYsBjR9s8mvjeugmoW1zL45u+xXNh8Sq1iFNYMuiMYJfCFyFY9OXNuYZdvz/k5jIj4gz4RyfdwCHClKiuYQ=="
        }
    }
}

# Little hack 'cause Azure doesn't return the IP address until it's assigned to a resource in that's running
# (https://github.com/terraform-providers/terraform-provider-azurerm/issues/310#issuecomment-327389965)
data "azurerm_public_ip" "datasourceip" {
  name = azurerm_public_ip.vmPublicIP.name
  resource_group_name = azurerm_virtual_machine.vm.resource_group_name
}

output "user" {
  value = azurerm_virtual_machine.vm.os_profile.admin_username
}

output "ip_address" {
  value = data.azurerm_public_ip.datasourceip.ip_address
}

# END OF VM SPECIFIC RESOURCES