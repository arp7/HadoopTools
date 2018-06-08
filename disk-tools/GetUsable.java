import java.io.*;

public class GetUsable {
  public static void main(String[] args) throws Exception {
    final File dir = new File(args[0]);
    System.out.println(dir.getUsableSpace());
  }
}
