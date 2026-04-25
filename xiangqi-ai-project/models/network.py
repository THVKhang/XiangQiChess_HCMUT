import torch
import torch.nn as nn
import torch.nn.functional as F

class ResBlock(nn.Module):
    """
    Residual Block (ResNet): Giúp mạng học được các đặc trưng sâu hơn mà không bị
    mất mát gradient (Vanishing Gradient). Nó cũng giúp tăng Receptive Field.
    """
    def __init__(self, channels=128):
        super(ResBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        out = F.relu(out)
        return out

class XiangQiResNet(nn.Module):
    def __init__(self, num_blocks=5, channels=128):
        """
        Kiến trúc mạng Value Network giống AlphaZero.
        - num_blocks: Số lượng Residual Blocks. 5 blocks = 10 lớp Conv, cho Receptive Field > 20x20.
        - channels: Số filter của mỗi lớp Conv.
        """
        super(XiangQiResNet, self).__init__()
        
        
        self.conv_input = nn.Conv2d(15, channels, kernel_size=3, padding=1, bias=False)
        self.bn_input = nn.BatchNorm2d(channels)
        
       
        self.res_blocks = nn.Sequential(
            *[ResBlock(channels) for _ in range(num_blocks)]
        )
        
        
        self.value_conv = nn.Conv2d(channels, 2, kernel_size=1, bias=False)
        self.value_bn = nn.BatchNorm2d(2)
        
        
        self.value_fc1 = nn.Linear(2 * 10 * 9, 256)
        self.value_fc2 = nn.Linear(256, 1)

    def forward(self, x):
        x = F.relu(self.bn_input(self.conv_input(x)))
        x = self.res_blocks(x)  
        v = F.relu(self.value_bn(self.value_conv(x))) 
        v = torch.flatten(v, 1) 
        v = F.relu(self.value_fc1(v))
        v = self.value_fc2(v)
        return torch.sigmoid(v)

if __name__ == "__main__":
    # Test script
    model = XiangQiResNet(num_blocks=5, channels=128)
    
    # Đếm số lượng tham số
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    dummy_input = torch.randn(4, 15, 10, 9)
    output = model(dummy_input)
    
    print("--- MODEL ARCHITECTURE ---")
    print(model)
    print(f"\nTotal Trainable Parameters: {total_params:,}")
    print("\n--- SHAPE TEST ---")
    print(f"Input shape : {dummy_input.shape} (Batch, Channels, Rows, Cols)")
    print(f"Output shape: {output.shape} (Batch, TargetValue)")
    print(f"Output Value: \n{output.detach().numpy()}")
